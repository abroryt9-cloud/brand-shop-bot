import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from flask import Flask
import threading

TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
PORT = 8080

# ---------- FLASK ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот работает и слушает порт 8080"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

threading.Thread(target=run_flask, daemon=True).start()

# ---------- БОТ ----------
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает! Ты сделал это!")

async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
