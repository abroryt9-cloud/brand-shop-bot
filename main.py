import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from flask import Flask, request
import sys

TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает! Ошибка 500 исправлена.")

# ---------- Flask для Webhook ----------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Bot is running", 200

@app.route('/', methods=['POST'])
def webhook():
    """Telegram присылает сюда обновления."""
    try:
        # Получаем JSON от Telegram
        update_data = request.json
        # Обрабатываем update синхронно через await в уже запущенном loop
        asyncio.run(dp.feed_update(bot, update_data))
        return "ok", 200
    except Exception as e:
        print(f"Ошибка в webhook: {e}", file=sys.stderr)
        return "error", 500

# ---------- Точка входа для Railway ----------
if __name__ == "__main__":
    # Запускаем Flask (блокирует поток)
    app.run(host='0.0.0.0', port=PORT)
