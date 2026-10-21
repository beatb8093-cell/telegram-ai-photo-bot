
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "សួស្តី! 👋 Welcome to AI Photo Enhancer.\n\n"
        "📷 សូមផ្ញើរូបភាពមកខ្ញុំ។\n"
        "ប្រព័ន្ធ AI កែលម្អរូបភាពនឹងត្រូវបានបន្ថែមក្នុងជំហានបន្ទាប់។"
    )

async def photo_received(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "📸 ខ្ញុំទទួលបានរូបភាពរបស់អ្នកហើយ!\n"
        "មុខងារ AI កែលម្អរូបភាពកំពុងរៀបចំ។"
    )

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_received))
    app.run_polling()

if __name__ == "__main__":
    main()
