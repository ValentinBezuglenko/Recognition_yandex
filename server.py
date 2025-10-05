import os
from flask import Flask, request, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = "/opt/render/project/wav_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/recognize", methods=["POST"])
def recognize():
    try:
        # принимаем бинарное тело
        audio_data = request.data
        if not audio_data or len(audio_data) < 100:
            return jsonify({"error": "No or too small file"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, "last.wav")
        with open(filepath, "wb") as f:
            f.write(audio_data)

        return jsonify({
            "status": "saved",
            "bytes_received": len(audio_data),
            "file": "last.wav"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/last", methods=["GET"])
def get_last():
    filepath = os.path.join(UPLOAD_FOLDER, "last.wav")
    if not os.path.exists(filepath):
        return jsonify({"error": "No file yet"}), 404
    return app.send_static_file(filepath)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
