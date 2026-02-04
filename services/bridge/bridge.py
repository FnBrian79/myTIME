"""
myTIME Dojo Bridge - FastAPI WebSocket service
Bridges the Foreman (Ollama text stream) to ElevenLabs real-time audio
and delivers audio to Android clients via WebSocket.

Supports Barge-In (Master-Student live mode) for 5x XP via Steward.
"""

import os
import json
import asyncio
import logging
import time
import uuid
from typing import Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
STEWARD_HOST = os.getenv("STEWARD_HOST", "http://steward:8080")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("dojo-bridge")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="myTIME Dojo Bridge", version="2.0.0")

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
# Session state (per-WebSocket connection)
# ---------------------------------------------------------------------------
class CombatSession:
    """Tracks the state of an active Combat Ring session."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.mode = "auto"  # auto | handoff | live
        self.user_id = "anonymous"
        self.caller_number = "unknown"
        self.persona = "hazel"
        self.start_time = time.time()
        self.barge_in_time = None
        self.live_seconds = 0
        self.auto_seconds = 0
        self.is_active = False
        self._cancel_event = asyncio.Event()

    def barge_in(self, user_id=None):
        if user_id:
            self.user_id = user_id
        self.mode = "live"
        self.barge_in_time = time.time()
        self._cancel_event.set()
        log.info("Session %s: BARGE-IN by %s", self.session_id, self.user_id)

    def barge_out(self):
        if self.barge_in_time:
            self.live_seconds += time.time() - self.barge_in_time
            self.barge_in_time = None
        self.mode = "auto"
        self._cancel_event.clear()
        log.info("Session %s: BARGE-OUT, live_seconds=%.1f", self.session_id, self.live_seconds)

    def end(self):
        if self.barge_in_time:
            self.live_seconds += time.time() - self.barge_in_time
            self.barge_in_time = None
        total = time.time() - self.start_time
        self.auto_seconds = total - self.live_seconds
        self.is_active = False

    @property
    def cancelled(self):
        return self._cancel_event.is_set()

    @property
    def total_duration(self):
        return int(time.time() - self.start_time)


# ---------------------------------------------------------------------------
# ElevenLabs helpers
# ---------------------------------------------------------------------------
async def elevenlabs_tts_stream(text: str, voice_id: str, model_id: str, cancel_event: asyncio.Event = None):
    """
    Stream audio bytes from ElevenLabs text-to-speech endpoint.
    Yields chunks of mp3 audio data. Stops early if cancel_event is set.
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
                if cancel_event and cancel_event.is_set():
                    log.info("TTS stream cancelled (barge-in)")
                    return
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


async def score_session(session: CombatSession):
    """
    Report the completed session to the Steward for XP/credit calculation.
    The Steward's log_call method applies mode multipliers:
      - auto: 1x
      - handoff: 2x
      - live: 5x (Master-Student bonus)
    """
    payload = {
        "user_id": session.user_id,
        "session_id": session.session_id,
        "duration_seconds": session.total_duration,
        "mode": "live" if session.live_seconds > 0 else "auto",
        "scam_type": "combat_ring",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{STEWARD_HOST}/api/log_call",
                json=payload,
            )
            if resp.status_code == 200:
                return resp.json()
            log.warning("Steward scoring failed: %s", resp.text)
    except Exception as e:
        log.warning("Steward unreachable for scoring: %s", e)
    return None


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "dojo-bridge", "version": "2.0.0"}


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
      {"action": "tts", "text": "...", "voice_id": "...", "model_id": "..."}
      {"action": "combat", "caller_number": "...", "transcript": "...", "persona": "..."}
      {"action": "barge_in", "user_id": "..."}   -> Human takes over (5x XP)
      {"action": "barge_out", "persona": "..."}   -> AI resumes
      {"action": "end_session"}                    -> Score & close

    Responses:
      Binary audio chunks during TTS streaming
      {"status": "streaming", ...}     - Combat started, TTS in progress
      {"status": "done"}               - Audio stream finished
      {"status": "barge_in_ack", ...}  - Barge-in confirmed
      {"status": "barge_out_ack", ...} - Barge-out confirmed
      {"status": "session_scored", ...} - Steward scoring result
    """
    await ws.accept()
    log.info("WebSocket client connected")

    session = CombatSession()
    session.is_active = True

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            action = msg.get("action", "tts")

            # ---------------------------------------------------------------
            # BARGE-IN: Human takes over
            # ---------------------------------------------------------------
            if action == "barge_in":
                session.barge_in(user_id=msg.get("user_id"))
                await ws.send_json({
                    "status": "barge_in_ack",
                    "session_id": session.session_id,
                    "mode": "live",
                    "xp_multiplier": 5,
                    "message": "You have the conn. 5x XP active.",
                })
                continue

            # ---------------------------------------------------------------
            # BARGE-OUT: Hand back to AI
            # ---------------------------------------------------------------
            if action == "barge_out":
                session.barge_out()
                new_persona = msg.get("persona", session.persona)
                session.persona = new_persona
                await ws.send_json({
                    "status": "barge_out_ack",
                    "mode": "auto",
                    "persona": new_persona,
                    "live_seconds": int(session.live_seconds),
                    "message": f"AI resuming as {new_persona}.",
                })
                continue

            # ---------------------------------------------------------------
            # END SESSION: Score via Steward
            # ---------------------------------------------------------------
            if action == "end_session":
                session.end()
                score = await score_session(session)
                await ws.send_json({
                    "status": "session_scored",
                    "session_id": session.session_id,
                    "total_duration": session.total_duration,
                    "live_seconds": int(session.live_seconds),
                    "auto_seconds": int(session.auto_seconds),
                    "steward": score,
                })
                # Reset for next session
                session = CombatSession()
                session.is_active = True
                continue

            # ---------------------------------------------------------------
            # COMBAT: Full cycle with barge-in-aware TTS
            # ---------------------------------------------------------------
            voice = msg.get("voice_id", ELEVENLABS_VOICE_ID)
            model = msg.get("model_id", ELEVENLABS_MODEL_ID)

            if not ELEVENLABS_API_KEY or not voice:
                await ws.send_json({"error": "ElevenLabs not configured"})
                continue

            if action == "combat":
                caller = msg.get("caller_number", "unknown")
                transcript = msg.get("transcript", "")
                persona = msg.get("persona", "hazel")

                session.caller_number = caller
                session.persona = persona

                triage = await triage_call(caller)
                actor_text = await get_actor_response(transcript, persona)

                await ws.send_json({
                    "status": "streaming",
                    "session_id": session.session_id,
                    "triage": triage,
                    "actor_text": actor_text,
                    "mode": session.mode,
                })

                text_to_speak = actor_text
            else:
                # Direct TTS
                text_to_speak = msg.get("text", "")

            if not text_to_speak:
                await ws.send_json({"error": "No text provided"})
                continue

            # Stream audio chunks (cancellable via barge-in)
            session._cancel_event.clear()
            async for chunk in elevenlabs_tts_stream(
                text_to_speak, voice, model, session._cancel_event
            ):
                await ws.send_bytes(chunk)

            if session.cancelled:
                await ws.send_json({"status": "stream_interrupted", "reason": "barge_in"})
            else:
                await ws.send_json({"status": "done"})

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
        if session.is_active:
            session.end()
            await score_session(session)
    except Exception as e:
        log.exception("WebSocket error: %s", e)
        try:
            await ws.send_json({"error": str(e)})
        except Exception:
            pass
