from flask import Flask, request, jsonify, send_file
import os
import time

app = Flask(__name__)

AUDIO_DIR = "recordings"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Временный буфер
audio_buffer = bytearray()
record_counter = 0
last_chunk_time = 0
CHUNK_TIMEOUT = 2.0  # секунда без новых данных = запись закончена

@app.route("/recognize", methods=["POST"])
def recognize():
    global audio_buffer, last_chunk_time

    if request.content_type != "audio/wav":
        return jsonify({"error": "Invalid content type"}), 400

    chunk = request.data
    if len(chunk) == 0:
        return jsonify({"error": "No audio data"}), 400

    audio_buffer.extend(chunk)
    last_chunk_time = time.time()
    return jsonify({"status": "chunk received", "chunk_bytes": len(chunk)})

@app.route("/recognize/flush", methods=["POST"])
def flush():
    global audio_buffer, record_counter

    if len(audio_buffer) == 0:
        return jsonify({"error": "No audio recorded"}), 400

    record_counter += 1
    filename = os.path.join(AUDIO_DIR, f"recording_{record_counter}.wav")
    with open(filename, "wb") as f:
        f.write(audio_buffer)

    size = len(audio_buffer)
    audio_buffer = bytearray()  # очищаем буфер после сохранения

    return jsonify({"status": "saved", "filename": filename, "bytes_received": size})

@app.route("/recordings/<name>", methods=["GET"])
def download_file(name):
    path = os.path.join(AUDIO_DIR, name)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
