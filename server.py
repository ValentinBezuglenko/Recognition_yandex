# server.py
from flask import Flask, request, jsonify
import os
import requests
import logging
import time
import random

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Берём ключ Yandex из переменных окружения на Render
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
if not YANDEX_API_KEY:
    logging.warning("YANDEX_API_KEY not set in environment — requests will fail without key.")

# Yandex synchronous STT endpoint
YANDEX_SYNC_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

# Пер-client простая защита: минимальный интервал между запросами (сек)
MIN_INTERVAL = 1.5
_LAST_CALL = {}

def client_allowed(client_id):
    now = time.time()
    last = _LAST_CALL.get(client_id, 0)
    if now - last < MIN_INTERVAL:
        return False, MIN_INTERVAL - (now - last)
    _LAST_CALL[client_id] = now
    return True, 0

def yandex_transcribe_bytes(wav_bytes, api_key, max_retries=4, base_delay=1.0):
    """
    Отправляет wav (bytes) в Yandex sync endpoint.
    При 429 или сетевой ошибке — повторяет с экспоненциальной backoff и jitter.
    Возвращает dict с результатом (или {'error': ...})
    """
    headers = {"Authorization": f"Api-Key {api_key}", "Content-Type": "audio/wav"}
    params = {"lang": "ru-RU"}  # поменяйте на нужный язык, например "en-US"
    attempt = 0

    while True:
        attempt += 1
        try:
            resp = requests.post(YANDEX_SYNC_URL, params=params, headers=headers, data=wav_bytes, timeout=60)
        except requests.RequestException as e:
            logging.warning("Network error to Yandex on attempt %d: %s", attempt, e)
            resp = None

        if resp is not None and resp.status_code == 200:
            # Yandex may return JSON or plain text depending on API version/config.
            try:
                j = resp.json()
            except Exception:
                j = {"raw_text": resp.text}
            # Normalise transcription field:
            transcription = j.get("result") or j.get("text") or j.get("raw_text") or ""
            return {"transcription": transcription, "yandex_raw": j}
        # Handle retry conditions
        status = resp.status_code if resp is not None else None
        if attempt >= max_retries:
            detail = resp.text if resp is not None else "no response"
            logging.error("Max retries reached. Last status: %s", status)
            return {"error": f"yandex_failed status={status} detail={detail}"}

        # compute delay; honor Retry-After if provided
        retry_after = None
        if resp is not None:
            retry_after = resp.headers.get("Retry-After")
        delay = base_delay * (2 ** (attempt - 1))
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except:
                pass
        jitter = random.uniform(0, 0.5 * delay)
        delay = delay + jitter
        logging.info("Yandex returned status=%s on attempt %d; sleeping %.1f s before retry", status, attempt, delay)
        time.sleep(delay)


@app.route("/recognize", methods=["POST"])
def recognize():
    # Проверяем ключ в окружении
    api_key = YANDEX_API_KEY
    if not api_key:
        return jsonify({"error": "Server has no YANDEX_API_KEY configured"}), 500

    client = request.remote_addr or "unknown"
    allowed, wait = client_allowed(client)
    if not allowed:
        return jsonify({"error": "rate_limited", "retry_after": wait}), 429

    data = request.data
    if not data:
        return jsonify({"error": "No file provided"}), 400

    # Вызов в Yandex
    result = yandex_transcribe_bytes(data, api_key, max_retries=4, base_delay=1.0)
    if "error" in result:
        return jsonify({"error": result["error"]}), 502

    return jsonify({"status": "ok", "transcription": result.get("transcription", ""), "yandex_raw": result.get("yandex_raw")})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
