import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# --- Hardcoded config (only the API key lives in Render's env vars) ---
ALLOWED_ORIGIN = "*"  # tighten this to your Cloudflare Pages URL once you have it, e.g. "https://your-project.pages.dev"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "qwen/qwen3-30b-a3b:free"

CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGIN}})

# Only this one comes from Render's environment settings
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

SYSTEM_PROMPT = (
    "You are a helpful AI assistant running on a Qwen model. "
    "Keep answers concise and clear."
)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": OPENROUTER_MODEL})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "Server missing OPENROUTER_API_KEY"}), 500

    data = request.get_json(silent=True) or {}
    user_messages = data.get("messages", [])

    if not user_messages or not isinstance(user_messages, list):
        return jsonify({"error": "Request must include a non-empty 'messages' list"}), 400

    payload_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_messages

    try:
        resp = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": ALLOWED_ORIGIN,
                "X-Title": "Qwen Chat MVP",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": payload_messages,
                "temperature": 0.7,
            },
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        reply = result["choices"][0]["message"]["content"]
        return jsonify({"reply": reply, "model": OPENROUTER_MODEL})

    except requests.exceptions.HTTPError:
        return jsonify({"error": "Upstream API error", "detail": resp.text}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
