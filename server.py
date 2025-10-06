from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Яндекс API ключ хранится на сервере через переменную окружения
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
YANDEX_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?lang=ru-RU"

@app.route("/recognize", methods=["POST"])
def recognize():
    if request.content_type != "audio/wav":
        return jsonify({"error": "Invalid content type"}), 400

    audio = request.data
    if len(audio) == 0:
        return jsonify({"error": "No audio data"}), 400

    try:
        # Отправляем на Яндекс как файл через multipart/form-data
        files = {"file": ("audio.wav", audio, "audio/x-wav")}
        headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}

        response = requests.post(YANDEX_URL, headers=headers, files=files)
        response.raise_for_status()
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
