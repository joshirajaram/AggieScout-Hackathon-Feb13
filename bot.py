import asyncio
import logging
import os
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from llm_engine import generate_alert_async
from council_engine import run_council

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 **AggieCouncil Online.**\n"
        "Status: Local Inference Active.\n"
        "Send a photo + caption for the Council, or text for alerts."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action="typing")
    try:
        response = await generate_alert_async(user_text)
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action="typing")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        buf = BytesIO()
        await file.download_to_memory(buf)
        buf.seek(0)
        image_bytes = buf.read()
        user_text = (update.message.caption or "Should I spray today?").strip()
        response = await asyncio.to_thread(
            run_council, user_text, image_bytes
        )
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Council Error: {str(e)}")

if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise SystemExit('Missing TELEGRAM_BOT_TOKEN in .env')
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("AggieCouncil Bot is running...")
    application.run_polling()
