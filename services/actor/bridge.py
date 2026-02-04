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
INTERRUPT_THRESHOLD = 500  # RMS energy threshold for barge-in detection

client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

def calculate_energy(audio_data):
    """Calculates RMS energy of raw SLIN audio (16-bit)."""
    import struct
    if not audio_data: return 0
    count = len(audio_data) // 2
    format = "<" + "h" * count
    shorts = struct.unpack(format, audio_data)
    sum_squares = sum(s*s for s in shorts)
    return (sum_squares / count) ** 0.5

async def handle_asterisk_connection(reader, writer):
    print("🚀 Scammer connected to the Dojo.")
    
    # Task to read from scammer (Barge-in detection)
    async def read_from_scammer():
        while True:
            try:
                data = await reader.read(320) # 20ms of audio @ 8kHz SLIN
                if not data: break
                
                energy = calculate_energy(data)
                if energy > INTERRUPT_THRESHOLD:
                    print(f"🔥 [BARGE-IN] Scammer energy detected: {energy:.2f}")
                    # Signal the write task to pivot or pause
                    # This would ideally cancel the current stream and start a "Soft Interrupt"
            except Exception as e:
                print(f"Read error: {e}")
                break

    # Task to write to scammer (AI Voice)
    async def write_to_scammer():
        response_text = "Wait, hold on... you said you're from where? My dog Steve just stepped on my keyboard."
        try:
            async for audio_chunk in client.generate(
                text=response_text, 
                voice=VOICE_ID, 
                model=voice_config.get("model_id", "eleven_flash_v2_5"),
                stream=True
            ):
                writer.write(audio_chunk)
                await writer.drain()
        except Exception as e:
            print(f"Write error: {e}")

    # Run read and write tasks concurrently
    await asyncio.gather(read_from_scammer(), write_to_scammer())
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
