"""
myTIME Dojo Bridge - FastAPI WebSocket service
Bridges the Foreman (Ollama text stream) to ElevenLabs real-time audio
and delivers audio to Android clients via WebSocket.
"""

import os
import json
import asyncio
import logging
from typing import Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_monolingual_v1")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
ACTOR_HOST = os.getenv("ACTOR_HOST", "http://actor:8000")
FOREMAN_HOST = os.getenv("FOREMAN_HOST", "http://triage-api:8080")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("dojo-bridge")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="myTIME Dojo Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    """Direct text-to-speech request."""
    text: str
    voice_id: Optional[str] = None
    model_id: Optional[str] = None


class CombatRequest(BaseModel):
    """Trigger a full Combat Ring cycle: Foreman -> Actor -> ElevenLabs."""
    caller_number: str
    transcript: str
    persona: Optional[str] = "hazel"


# ---------------------------------------------------------------------------
# ElevenLabs helpers
# ---------------------------------------------------------------------------
async def elevenlabs_tts_stream(text: str, voice_id: str, model_id: str):
    """
    Stream audio bytes from ElevenLabs text-to-speech endpoint.
    Yields chunks of mp3 audio data.
    """
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                log.error("ElevenLabs error %s: %s", resp.status_code, body.decode())
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"ElevenLabs API error: {body.decode()}",
                )
            async for chunk in resp.aiter_bytes(chunk_size=1024):
                yield chunk


async def get_actor_response(transcript: str, persona: str) -> str:
    """Ask the Actor service for a persona-driven response."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{ACTOR_HOST}/respond",
            json={"transcript": transcript, "persona": persona},
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


async def triage_call(caller_number: str) -> dict:
    """Hit the Foreman triage API to classify the incoming call."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{FOREMAN_HOST}/triage",
            json={"number": caller_number},
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "dojo-bridge"}


@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    """
    One-shot TTS: returns full audio as mp3.
    Primarily for testing; the WebSocket endpoint is preferred for streaming.
    """
    voice = req.voice_id or ELEVENLABS_VOICE_ID
    model = req.model_id or ELEVENLABS_MODEL_ID

    if not ELEVENLABS_API_KEY or not voice:
        raise HTTPException(status_code=500, detail="ElevenLabs not configured")

    chunks = []
    async for chunk in elevenlabs_tts_stream(req.text, voice, model):
        chunks.append(chunk)

    from fastapi.responses import Response

    return Response(content=b"".join(chunks), media_type="audio/mpeg")


@app.post("/combat")
async def combat_endpoint(req: CombatRequest):
    """
    Full Combat Ring cycle (REST version):
    1. Triage the caller number
    2. Get Actor persona response
    3. Return text + metadata (audio via WebSocket)
    """
    triage = await triage_call(req.caller_number)
    actor_text = await get_actor_response(req.transcript, req.persona)

    return {
        "triage": triage,
        "actor_response": actor_text,
        "persona": req.persona,
        "hint": "Connect via WebSocket at /ws/stream for real-time audio",
    }


# ---------------------------------------------------------------------------
# WebSocket: Real-time audio stream to Android client
# ---------------------------------------------------------------------------
@app.websocket("/ws/stream")
async def ws_audio_stream(ws: WebSocket):
    """
    WebSocket endpoint for the Android client.

    Protocol:
    1. Client sends JSON: {"action": "tts", "text": "...", "voice_id": "...", "model_id": "..."}
       OR: {"action": "combat", "caller_number": "...", "transcript": "...", "persona": "..."}
    2. Server streams binary audio chunks back.
    3. Server sends JSON: {"status": "done"} when the stream is complete.
    """
    await ws.accept()
    log.info("WebSocket client connected")

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            action = msg.get("action", "tts")

            voice = msg.get("voice_id", ELEVENLABS_VOICE_ID)
            model = msg.get("model_id", ELEVENLABS_MODEL_ID)

            if not ELEVENLABS_API_KEY or not voice:
                await ws.send_json({"error": "ElevenLabs not configured"})
                continue

            if action == "combat":
                # Full combat cycle: triage -> actor -> TTS
                caller = msg.get("caller_number", "unknown")
                transcript = msg.get("transcript", "")
                persona = msg.get("persona", "hazel")

                triage = await triage_call(caller)
                actor_text = await get_actor_response(transcript, persona)

                await ws.send_json({
                    "status": "streaming",
                    "triage": triage,
                    "actor_text": actor_text,
                })

                text_to_speak = actor_text
            else:
                # Direct TTS
                text_to_speak = msg.get("text", "")

            if not text_to_speak:
                await ws.send_json({"error": "No text provided"})
                continue

            # Stream audio chunks
            async for chunk in elevenlabs_tts_stream(text_to_speak, voice, model):
                await ws.send_bytes(chunk)

            await ws.send_json({"status": "done"})

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
    except Exception as e:
        log.exception("WebSocket error: %s", e)
        try:
            await ws.send_json({"error": str(e)})
        except Exception:
            pass
