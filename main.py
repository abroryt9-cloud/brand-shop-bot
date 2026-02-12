import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот работает!")

async def main():
    print("✅ Бот запущен и работает")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
