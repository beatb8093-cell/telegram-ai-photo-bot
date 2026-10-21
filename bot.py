
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")


def telegram_api(method, data):
    if not TOKEN:
        return None

    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        return requests.post(url, json=data, timeout=20)
    except requests.RequestException:
        return None


@app.get("/")
def home():
    return "AI Photo Enhancer Bot is running!"


@app.post("/telegram-webhook")
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message")

    if not message:
        return jsonify(ok=True)

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return jsonify(ok=True)

    text = message.get("text", "")

    if text.startswith("/start"):
        reply = (
            "សួស្តី! 👋 Welcome to AI Photo Enhancer.\n\n"
            "📷 សូមផ្ញើរូបភាពមកខ្ញុំ។\n"
            "AI photo enhancement is being prepared!"
        )
        telegram_api("sendMessage", {
            "chat_id": chat_id,
            "text": reply
        })

    elif message.get("photo"):
        telegram_api("sendMessage", {
            "chat_id": chat_id,
            "text": (
                "📸 ខ្ញុំទទួលបានរូបភាពរបស់អ្នកហើយ!\n"
                "មុខងារ AI កែលម្អរូបភាពនឹងត្រូវបានបន្ថែមបន្ទាប់។"
            )
        })

    return jsonify(ok=True)


if TOKEN and WEBHOOK_URL:
    telegram_api("setWebhook", {
        "url": WEBHOOK_URL.rstrip("/") + "/telegram-webhook"
    })
    if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

