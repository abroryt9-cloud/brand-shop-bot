import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from flask import Flask
import threading
import os

TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает! Проблема была в коде, а не в настройках.")

# ---------- FLASK ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

threading.Thread(target=run_flask, daemon=True).start()

async def main():
    await bot.delete_webhook()
    await bot.set_webhook(url="https://brand-shop-bot-production.up.railway.app/")
    print("✅ Webhook set")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
