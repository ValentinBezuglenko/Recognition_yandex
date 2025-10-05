import os
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = "/opt/render/project/wav_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
FILEPATH = os.path.join(UPLOAD_FOLDER, "last.wav")

@app.route("/recognize", methods=["POST"])
def recognize():
    audio_data = request.data
    if not audio_data or len(audio_data) < 100:
        return jsonify({"error": "No or too small file"}), 400

    with open(FILEPATH, "wb") as f:
        f.write(audio_data)

    print(f"Saved {len(audio_data)} bytes to {FILEPATH}")
    return jsonify({"status": "saved", "bytes_received": len(audio_data)})

@app.route("/last", methods=["GET"])
def get_last():
    if not os.path.exists(FILEPATH):
        return jsonify({"error": "No file yet"}), 404
    return send_file(FILEPATH, mimetype="audio/wav", as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
