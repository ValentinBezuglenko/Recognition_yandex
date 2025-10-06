from flask import Flask, request, jsonify, send_file
import os, struct

app = Flask(__name__)

AUDIO_DIR = "recordings"
os.makedirs(AUDIO_DIR, exist_ok=True)

audio_buffer = bytearray()
record_counter = 0

SAMPLE_RATE = 16000
NUM_CHANNELS = 1
BITS_PER_SAMPLE = 16

def write_wav_header(filename, pcm_size):
    with open(filename, "wb") as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + pcm_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', NUM_CHANNELS))
        f.write(struct.pack('<I', SAMPLE_RATE))
        byte_rate = SAMPLE_RATE * NUM_CHANNELS * BITS_PER_SAMPLE // 8
        f.write(struct.pack('<I', byte_rate))
        block_align = NUM_CHANNELS * BITS_PER_SAMPLE // 8
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', BITS_PER_SAMPLE))
        f.write(b'data')
        f.write(struct.pack('<I', pcm_size))

@app.route("/recognize", methods=["POST"])
def recognize():
    global audio_buffer
    chunk = request.data
    if len(chunk) == 0:
        return jsonify({"error": "No audio data"}), 400
    audio_buffer.extend(chunk)
    return jsonify({"status": "chunk received", "chunk_bytes": len(chunk)})

@app.route("/recognize/flush", methods=["POST"])
def flush():
    global audio_buffer, record_counter
    if len(audio_buffer) == 0:
        return jsonify({"error": "No audio recorded"}), 400

    record_counter += 1
    filename = os.path.join(AUDIO_DIR, f"recording_{record_counter}.wav")
    write_wav_header(filename, len(audio_buffer))
    with open(filename, "ab") as f:
        f.write(audio_buffer)

    size = len(audio_buffer)
    audio_buffer = bytearray()
    return jsonify({"status": "saved", "filename": filename, "bytes_received": size})

@app.route("/recordings/<name>", methods=["GET"])
def download_file(name):
    path = os.path.join(AUDIO_DIR, name)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
