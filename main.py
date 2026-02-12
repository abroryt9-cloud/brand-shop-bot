import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

import sqlite3
from datetime import datetime
from flask import Flask
import threading

# ------------------------------------------------------
# ТВОИ ДАННЫЕ - ВСТАВЬ СЮДА
# ------------------------------------------------------
TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
ADMIN_ID = 6660842028   # ТВОЙ ID ЦИФРАМИ
# ------------------------------------------------------

app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, username TEXT, items TEXT,
                  name TEXT, phone TEXT, address TEXT,
                  total INTEGER, status TEXT, date TEXT)''')
    conn.commit()
    conn.close()
init_db()

# ---------- СТАРТ ----------
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        "Это бот бренда.\n"
        "Пока тут просто тест. Если ты это видишь — бот РАБОТАЕТ."
    )

# ---------- ЗАПУСК ----------
async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
