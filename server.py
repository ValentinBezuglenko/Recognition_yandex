import asyncio
import websockets
import wave
import os
from datetime import datetime

# ===== Папка для WAV =====
AUDIO_DIR = "recordings"
os.makedirs(AUDIO_DIR, exist_ok=True)

# ===== Параметры аудио =====
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit

# ===== Обработчик WebSocket =====
async def handler(websocket):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(AUDIO_DIR, f"recording_{timestamp}.wav")

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(SAMPLE_WIDTH)
    wf.setframerate(SAMPLE_RATE)

    print(f"Recording started: {filename}")
    try:
        async for message in websocket:
            # message уже бинарный PCM
            wf.writeframes(message)
    except websockets.exceptions.ConnectionClosedOK:
        pass
    finally:
        wf.close()
        print(f"Recording saved: {filename}")

# ===== Основная функция =====
async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("WebSocket server listening on port 8765...")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
