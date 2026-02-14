import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from llm_engine import generate_alert_async

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 **AggieScout Online.**\n"
        "Status: Local Inference Active.\n"
        "Monitoring field sensors."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action="typing")
    try:
        response = await generate_alert_async(user_text)
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token('8578782102:AAFFUrbFWvLY4ujNYUev2D2S3B1Oaa8Cy80').build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("AggieScout Bot is running...")
    application.run_polling()
