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

# Глобальный event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает! Ошибка event loop исправлена.")

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = Update(**request.json)
        # Используем глобальный loop
        asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
        return "ok", 200
    return "✅ Bot is running", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def run_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.start_polling(bot))

# Запускаем Flask в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

# Запускаем бота в отдельном потоке с event loop
threading.Thread(target=run_bot, daemon=True).start()

# Держим главный поток живым
threading.Event().wait()
