import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command
from flask import Flask, request, jsonify
import threading
import os

TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает!")

# ---------- FLASK ДЛЯ WEBHOOK ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот запущен. Webhook URL: /webhook"

@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    update = Update(**json_data)
    asyncio.create_task(dp.feed_update(bot, update))
    return "ok"

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# ---------- УСТАНОВКА ВЕБХУКА ----------
async def set_webhook():
    url = f"https://brand-shop-bot-production.up.railway.app/webhook"
    await bot.set_webhook(url=url)
    print(f"✅ Webhook set to {url}")

if __name__ == "__main__":
    asyncio.run(set_webhook())
    asyncio.run(dp.start_polling(bot))
