import os
import time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# Папка для хранения записей
UPLOAD_FOLDER = "recordings"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Буфер для накопления аудио
audio_buffer = bytearray()


def write_wav_header(filename, pcm_size, sample_rate=16000, bits_per_sample=16, channels=1):
    """Записывает WAV-заголовок + резерв под данные"""
    with open(filename, "wb") as f:
        f.write(b"RIFF")
        f.write((36 + pcm_size).to_bytes(4, "little"))
        f.write(b"WAVE")

        # fmt subchunk
        f.write(b"fmt ")
        f.write((16).to_bytes(4, "little"))  # Subchunk1Size
        f.write((1).to_bytes(2, "little"))   # PCM format
        f.write((channels).to_bytes(2, "little"))
        f.write((sample_rate).to_bytes(4, "little"))
        byte_rate = sample_rate * channels * bits_per_sample // 8
        f.write((byte_rate).to_bytes(4, "little"))
        block_align = channels * bits_per_sample // 8
        f.write((block_align).to_bytes(2, "little"))
        f.write((bits_per_sample).to_bytes(2, "little"))

        # data subchunk
        f.write(b"data")
        f.write((pcm_size).to_bytes(4, "little"))


@app.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    global audio_buffer
    chunk = request.data
    if not chunk:
        return jsonify({"error": "empty chunk"}), 400

    audio_buffer.extend(chunk)
    return jsonify({"status": "chunk received", "chunk_bytes": len(chunk)})


@app.route("/flush", methods=["POST"])
def flush():
    global audio_buffer
    pcm_size = len(audio_buffer)

    if pcm_size < 1000:  # меньше 1000 байт — отбрасываем
        audio_buffer = bytearray()
        return jsonify({"error": "too short recording"}), 400

    # уникальное имя по времени
    filename = f"recording_{int(time.time())}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Записываем WAV
    write_wav_header(filepath, pcm_size)
    with open(filepath, "ab") as f:
        f.write(audio_buffer)

    # очищаем буфер
    audio_buffer = bytearray()

    return jsonify({
        "status": "saved",
        "bytes_received": pcm_size,
        "filename": filename,
        "url": f"/recordings/{filename}"
    })


@app.route("/recordings/<filename>")
def serve_recording(filename):
    """Отдаём wav файл по ссылке"""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/")
def index():
    return "🎙️ Speech server is running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
