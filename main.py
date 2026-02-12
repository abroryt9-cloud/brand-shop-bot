import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from flask import Flask
import threading

# ------------------------------------------------------
TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
PORT = 8080
# ------------------------------------------------------

# ---------- FLASK-ЗАГЛУШКА (RAILWAY НЕ УПАДЁТ) ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running on port 8080"

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

thread = threading.Thread(target=run_flask, daemon=True)
thread.start()

# ---------- БОТ ----------
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает! Ты сделал это!")

# ---------- ЗАПУСК ----------
async def main():
    print("✅ Бот запущен и слушает порт", PORT)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
