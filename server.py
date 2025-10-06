import asyncio
import websockets
import wave

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit

async def handler(websocket, path):
    filename = "recording_stream.wav"
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(SAMPLE_WIDTH)
    wf.setframerate(SAMPLE_RATE)

    try:
        async for message in websocket:
            wf.writeframes(message)
    finally:
        wf.close()
        print("Saved WAV:", filename)

start_server = websockets.serve(handler, '0.0.0.0', 8765)  # порт 8765 для теста

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
