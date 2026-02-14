import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Import the logic from your teammate's file
from llm_engine import generate_alert

# Enable logging to see errors in the terminal
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initializes the connection and confirms the local node is active."""
    await update.message.reply_text(
        "🌿 **AggieScout Online.**\n"
        "Status: Local Inference Active (Cactus Engine).\n"
        "Monitoring field sensors... No cell service required."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captures user voice/text and routes it through the local LLM logic."""
    user_text = update.message.text
    
    # Show a 'typing' state to the user while the local model infers
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action="typing")
    
    try:
        # Pass the message to your backend engine
        response = await generate_alert(user_text)
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Local Node Error: {str(e)}")

if __name__ == '__main__':
    # REPLACE 'YOUR_HTTP_API_TOKEN' with the token from @BotFather
    application = ApplicationBuilder().token('8578782102:AAFFUrbFWvLY4ujNYUev2D2S3B1Oaa8Cy80').build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    
    print("AggieScout Bot is running...")
    application.run_polling()