import asyncio
import websockets
import json
import base64
import os
import yaml
from elevenlabs.client import AsyncElevenLabs

# Load settings
CONFIG_PATH = os.environ.get("VOICE_CONFIG", "../../config/voice_settings.yaml")
with open(CONFIG_PATH, "r") as f:
    voice_config = yaml.safe_load(f)

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "your_api_key")
VOICE_ID = voice_config.get("voice_id", "your_brian_clone_id")
ASTERISK_IP = "0.0.0.0"
AUDIOSOCKET_PORT = int(os.environ.get("AUDIOSOCKET_PORT", 9092))

client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

async def handle_asterisk_connection(reader, writer):
    print("🚀 Scammer connected to the Dojo.")
    
    # Example handover context from Ollama (this would be dynamic in production)
    response_text = "Wait, hold on... you said you're from where? My dog Steve just stepped on my keyboard."
    
    try:
        async for audio_chunk in client.generate(
            text=response_text, 
            voice=VOICE_ID, 
            model=voice_config.get("model_id", "eleven_flash_v2_5"),
            stream=True
        ):
            # AudioSocket expects raw SLIN (16-bit Signed Linear)
            # TBD: Conversion layer for raw AudioSocket format
            writer.write(audio_chunk)
            await writer.drain()
            
    except Exception as e:
        print(f"❌ Voice Bridge Error: {e}")
    finally:
        print("🔌 Session Ended.")
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_asterisk_connection, ASTERISK_IP, AUDIOSOCKET_PORT)
    addr = server.sockets[0].getsockname()
    print(f"📡 AudioSocket Bridge serving on {addr}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
