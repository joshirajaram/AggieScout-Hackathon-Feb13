import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Import the logic from your teammate's file
from llm_engine import generate_response, check_for_alerts

# Enable logging to see errors in the terminal
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initializes the connection and confirms the local node is active."""
    # Store chat_id to send proactive alerts
    context.job_queue.run_repeating(alarm, interval=10, first=5, chat_id=update.message.chat_id)
    
    await update.message.reply_text(
        "🌿 **AggieScout Online.**\n"
        "Status: Active Monitoring.\n"
        "I will check sensors every 10 seconds and alert you of any issues."
    )

async def alarm(context: ContextTypes.DEFAULT_TYPE):
    """Periodic task to check for sensor anomalies and alert the user."""
    job = context.job
    alert_message = await check_for_alerts()
    if alert_message:
        await context.bot.send_message(job.chat_id, text=f"🚨 **AUTONOMOUS ALERT** 🚨\n\n{alert_message}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captures user voice/text and routes it through the local LLM logic."""
    user_text = update.message.text
    
    # Show a 'typing' state to the user while the local model infers
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action="typing")
    
    try:
        # Pass the message to your backend engine
        response = await generate_response(user_text)
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