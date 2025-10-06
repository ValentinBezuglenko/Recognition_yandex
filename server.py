import socket
import wave

HOST = '0.0.0.0'
PORT = 5005
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit

filename = "recording_from_esp32.wav"

# TCP сервер
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)
print("Waiting for ESP32 connection...")
conn, addr = sock.accept()
print(f"Connected: {addr}")

# WAV файл
wf = wave.open(filename, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(SAMPLE_WIDTH)
wf.setframerate(SAMPLE_RATE)

try:
    while True:
        data = conn.recv(3200*2)  # 3200 байт = 1600 сэмплов
        if not data:
            break
        wf.writeframes(data)
finally:
    conn.close()
    wf.close()
    print("Recording saved:", filename)
