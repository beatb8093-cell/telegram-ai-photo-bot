
import os
import io
import logging
import threading
import requests

from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{TOKEN}"
    if TOKEN else None
)

session = requests.Session()


def telegram_api(method, data=None, files=None):
    if not TELEGRAM_API:
        logging.error("Missing TELEGRAM_BOT_TOKEN")
        return None

    try:
        response = session.post(
            f"{TELEGRAM_API}/{method}",
            data=data,
            files=files,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            logging.error("Telegram API error: %s", result)

        return result

    except Exception:
        logging.exception("Telegram API request failed")
        return None


def enhance_image(image_bytes):
    """Improve natural color and sharpness without changing dimensions."""
    with Image.open(io.BytesIO(image_bytes)) as original:
        original.load()

        # Keep the original dimensions and orientation.
        image = ImageOps.exif_transpose(original)
        image = image.convert("RGB")

        # Improve contrast gently.
        image = ImageOps.autocontrast(image, cutoff=0.5)
        image = ImageEnhance.Color(image).enhance(1.10)
        image = ImageEnhance.Contrast(image).enhance(1.08)
        image = ImageEnhance.Brightness(image).enhance(1.03)

        # Sharpen details without resizing the image.
        image = image.filter(
            ImageFilter.UnsharpMask(
                radius=1.5,
                percent=125,
                threshold=3
            )
        )

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=95, optimize=True)
        output.seek(0)
        return output


def download_telegram_photo(file_id):
    result = telegram_api("getFile", {"file_id": file_id})

    if not result or not result.get("ok"):
        raise RuntimeError("Could not get Telegram file information")

    file_path = result["result"]["file_path"]
    url = f"{TELEGRAM_API}/../file/bot{TOKEN}/{file_path}"

    # Use Telegram's official file-download endpoint.
    url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

    response = session.get(url, timeout=60)
    response.raise_for_status()

    if len(response.content) > 15 * 1024 * 1024:
        raise ValueError("Photo is too large; please send a smaller image.")

    return response.content


def send_photo(chat_id, image_bytes):
    files = {
        "photo": ("enhanced.jpg", image_bytes, "image/jpeg")
    }
    data = {
        "chat_id": str(chat_id),
        "caption": (
            "✅ រូបភាពរបស់អ្នកបានកែលម្អរួចហើយ!\n"
            "ពណ៌ និងភាពច្បាស់ត្រូវបានកែលម្អ "
            "ដោយរក្សាទំហំរូបដើម។"
        )
    }
    return telegram_api("sendPhoto", data=data, files=files)


@app.get("/")
def home():
    return "AI Photo Enhancer Bot is running!"


@app.post("/telegram-webhook")
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}

    chat_id = (message.get("chat") or {}).get("id")
    if not chat_id:
        return jsonify(ok=True)

    text = message.get("text", "")

    if text.startswith("/start"):
        telegram_api("sendMessage", {
            "chat_id": chat_id,
            "text": (
                "សួស្តី! 👋 Welcome to Photo Enhancer.\n\n"
                "📷 សូមផ្ញើរូបភាពមកខ្ញុំ។\n"
                "ខ្ញុំនឹងកែលម្អពណ៌ និងភាពច្បាស់ "
                "ដោយព្យាយាមរក្សារូបរាងដើម។"
            )
        })
        return jsonify(ok=True)

    photos = message.get("photo")
    if photos:
        try:
            telegram_api("sendChatAction", {
                "chat_id": chat_id,
                "action": "upload_photo"
            })

            # Telegram lists photo sizes from smaller to larger.
            file_id = photos[-1]["file_id"]
            original_bytes = download_telegram_photo(file_id)
            enhanced = enhance_image(original_bytes)

            result = send_photo(chat_id, enhanced)

            if not result or not result.get("ok"):
                telegram_api("sendMessage", {
                    "chat_id": chat_id,
                    "text": "សូមអភ័យទោស! ខ្ញុំមិនអាចផ្ញើរូបត្រឡប់បានទេ។"
                })

        except Exception:
            logging.exception("Photo enhancement failed")
            telegram_api("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    "សូមអភ័យទោស! ការកែលម្អរូបភាពមានបញ្ហា។ "
                    "សូមសាកល្បងរូប JPG ឬ PNG ផ្សេងទៀត។"
                )
            })

        return jsonify(ok=True)

    telegram_api("sendMessage", {
        "chat_id": chat_id,
        "text": "📷 សូមផ្ញើរូបភាព JPG ឬ PNG ដើម្បីកែលម្អ។"
    })
    return jsonify(ok=True)


def set_webhook():
    if TOKEN and WEBHOOK_URL:
        result = telegram_api("setWebhook", {
            "url": WEBHOOK_URL + "/telegram-webhook"
        })
        logging.info("Webhook setup result: %s", result)


if __name__ == "__main__":
    threading.Thread(target=set_webhook, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
