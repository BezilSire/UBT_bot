import os
import threading
import asyncio
import nest_asyncio
from flask import Flask
from bot.main import start_bot  # Make sure this import matches your folder structure

# Apply nest_asyncio so we can use asyncio in a thread (needed for Flask + Bot together)
nest_asyncio.apply()

# Flask app setup
PORT = int(os.environ.get("PORT", 10000))
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Ubuntium Telegram bot is alive and running!"

# Start the bot in a background thread using a fresh event loop
def run_bot():
    print("🔁 Starting Telegram bot...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())
    print("❌ Bot stopped unexpectedly.")

# Entry point for Render
if __name__ == "__main__":
    print("🚀 Booting Flask server and Telegram bot...")
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=PORT)
