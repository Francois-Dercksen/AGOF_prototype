import os
import json
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)

ALLOWED_ORIGIN = "*"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "qwen/qwen3-30b-a3b"

CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGIN}})

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

SYSTEM_PROMPT = (
    "You are the AGOF assistant, embodying 'Success by Principle'. "
    "Keep answers concise, clear, and helpful."
)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "Server missing OPENROUTER_API_KEY"}), 500

    data = request.get_json(silent=True) or {}
    user_messages = data.get("messages", [])

    if not user_messages or not isinstance(user_messages, list):
        return jsonify({"error": "Request must include a non-empty 'messages' list"}), 400

    payload_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_messages

    def generate():
        try:
            with requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": payload_messages,
                    "temperature": 0.7,
                    "stream": True,
                },
                stream=True,
                timeout=120,
            ) as resp:
                resp.encoding = "utf-8"

                if resp.status_code != 200:
                    yield f"[ERROR] {resp.text}"
                    return

                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue
        except Exception as e:
            yield f"[ERROR] {str(e)}"

    return Response(stream_with_context(generate()), mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
