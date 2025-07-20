import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from bot.main import main as bot_main

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create a new asyncio event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Initialize Flask app
app = Flask(__name__)

# Asynchronously run the bot and get the application instance
application = loop.run_until_complete(bot_main())
bot = application.bot

async def set_webhook():
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        await bot.set_webhook(url=f"{webhook_url}/webhook")
        logger.info(f"Webhook set to {webhook_url}/webhook")
    else:
        logger.warning("WEBHOOK_URL not set, webhook not configured.")

@app.route("/")
def index():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "OK"

if __name__ == "__main__":
    loop.run_until_complete(set_webhook())
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
