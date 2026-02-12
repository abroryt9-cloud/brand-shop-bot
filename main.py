import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command
from flask import Flask, request
import threading

TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает! Ошибка 405 исправлена.")

# ---------- FLASK ПРИНИМАЕТ POST ----------
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = Update(**request.json)
        asyncio.create_task(dp.feed_update(bot, update))
        return "ok", 200
    return "✅ Бот работает", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

threading.Thread(target=run_flask, daemon=True).start()

# ---------- УСТАНОВКА ВЕБХУКА ----------
async def main():
    webhook_url = "https://brand-shop-bot-production.up.railway.app/"
    await bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set to {webhook_url}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
