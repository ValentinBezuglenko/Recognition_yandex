from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Яндекс API ключ хранится на сервере для безопасности
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")  # ставим через переменные окружения
YANDEX_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?lang=ru-RU"

@app.route("/recognize", methods=["POST"])
def recognize():
    if request.content_type != "audio/wav":
        return jsonify({"error": "Invalid content type"}), 400

    audio = request.data
    if len(audio) == 0:
        return jsonify({"error": "No audio data"}), 400

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }

    try:
        response = requests.post(YANDEX_URL, headers=headers, data=audio)
        response.raise_for_status()
        result = response.json()  # Yandex возвращает JSON с текстом
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
