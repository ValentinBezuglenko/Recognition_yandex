from flask import Flask, request, jsonify
import os, struct

app = Flask(__name__)
UPLOAD_FOLDER = "recordings"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

audio_buffer = bytearray()

def write_wav_header(filename, pcm_size, sample_rate=16000, num_channels=1, bits_per_sample=16):
    with open(filename, "wb") as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + pcm_size))  # Размер всего файла минус 8
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))             # Subchunk1Size
        f.write(struct.pack('<H', 1))              # PCM
        f.write(struct.pack('<H', num_channels))   # Channels
        f.write(struct.pack('<I', sample_rate))    # Sample rate
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        f.write(struct.pack('<I', byte_rate))      # Byte rate
        block_align = num_channels * bits_per_sample // 8
        f.write(struct.pack('<H', block_align))    # Block align
        f.write(struct.pack('<H', bits_per_sample))# Bits per sample
        f.write(b'data')
        f.write(struct.pack('<I', pcm_size))       # Data chunk size


@app.route("/stream", methods=["POST"])
def stream():
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

    if pcm_size < 3200:
        audio_buffer = bytearray()
        return jsonify({"error": "too short recording"}), 400

    filename = os.path.join(UPLOAD_FOLDER, "recording.wav")

    # Заголовок + PCM
    write_wav_header(filename, pcm_size)
    with open(filename, "ab") as f:
        f.write(audio_buffer)

    audio_buffer = bytearray()
    return jsonify({
        "status": "saved",
        "bytes_received": pcm_size,
        "filename": filename
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
