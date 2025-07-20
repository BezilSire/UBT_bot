# app.py
import os
import threading
import asyncio
import nest_asyncio
from flask import Flask
from bot.main import start_bot  # make sure this matches your folder structure

nest_asyncio.apply()

PORT = int(os.environ.get("PORT", 10000))
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Ubuntium Telegram bot is alive and running!"

def run_bot():
    asyncio.run(start_bot())

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=PORT)
