import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3
from datetime import datetime

# Состояния для заказа
class OrderState(StatesGroup):
    name = State()
    phone = State()
    address = State()

# Товары
products = {
    'shirt': {'name': 'Классическая рубашка', 'price': 11000, 'desc': 'Премиум-рубашка Old Money'},
    'zip': {'name': 'Олимпийка', 'price': 9900, 'desc': 'Трикотаж Old Money'}
}

# Инициализация
TOKEN = '8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng'
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)

# База данных
def init_db():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  items TEXT,
                  name TEXT,
                  phone TEXT,
                  address TEXT,
                  total INTEGER,
                  status TEXT,
                  date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Клавиатуры
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('🛍 Каталог'))
    kb.add(KeyboardButton('🛒 Корзина'), KeyboardButton('📦 Мои заказы'))
    return kb

# Корзина (в памяти)
user_carts = {}

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer(
        f'👋 Привет, {message.from_user.first_name}!\n'
        'Это бот бренда [НАЗВАНИЕ]. Здесь можно заказать премиум-одежду.',
        reply_markup=main_keyboard()
    )

@dp.message_handler(lambda message: message.text == '🛍 Каталог')
async def catalog(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for pid, prod in products.items():
        btn = InlineKeyboardButton(
            f"{prod['name']} — {prod['price']} ₽",
            callback_data=f'product_{pid}'
        )
        keyboard.add(btn)
    await message.answer('Выберите товар:', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('product_'))
async def show_product(callback: types.CallbackQuery):
    pid = callback.data.replace('product_', '')
    prod = products[pid]
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        '🛒 Добавить в корзину',
        callback_data=f'add_{pid}'
    ))
    
    await callback.message.edit_text(
        f"*{prod['name']}*\n\n"
        f"{prod['desc']}\n\n"
        f"Цена: {prod['price']} ₽",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith('add_'))
async def add_to_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pid = callback.data.replace('add_', '')
    
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    user_carts[user_id].append(pid)
    await callback.answer('✅ Товар добавлен в корзину')

@dp.message_handler(lambda message: message.text == '🛒 Корзина')
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        await message.answer('🛒 Корзина пуста')
        return
    
    total = 0
    text = '🛒 *Ваша корзина:*\n\n'
    for pid in cart:
        prod = products[pid]
        text += f"• {prod['name']} — {prod['price']} ₽\n"
        total += prod['price']
    
    text += f'\n*Итого: {total} ₽*'
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        '✅ Оформить заказ',
        callback_data='checkout'
    ))
    keyboard.add(InlineKeyboardButton(
        '🗑 Очистить',
        callback_data='clear_cart'
    ))
    
    await message.answer(text, parse_mode='Markdown', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'checkout')
async def checkout(callback: types.CallbackQuery):
    await OrderState.name.set()
    await callback.message.edit_text('Введите ваше имя:')

@dp.message_handler(state=OrderState.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await OrderState.phone.set()
    await message.answer('Введите номер телефона:')

@dp.message_handler(state=OrderState.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await OrderState.address.set()
    await message.answer('Введите адрес доставки:')

@dp.message_handler(state=OrderState.address)
async def process_address(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    cart = user_carts.get(user_id, [])
    
    # Считаем сумму
    total = sum(products[pid]['price'] for pid in cart)
    
    # Сохраняем в БД
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders 
        (user_id, username, items, name, phone, address, total, status, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        message.from_user.username or '',
        ','.join(cart),
        data['name'],
        data['phone'],
        message.text,
        total,
        'новый',
        datetime.now().isoformat()
    ))
    conn.commit()
    order_id = c.lastrowid
    conn.close()
    
    # Очищаем корзину
    user_carts[user_id] = []
    
    # Отправляем тебе уведомление
    await bot.send_message(
        chat_id='6660842028,  # СЮДА ТВОЙ ID
        text=f"📦 *НОВЫЙ ЗАКАЗ #{order_id}*\n\n"
             f"👤 Имя: {data['name']}\n"
             f"📞 Телефон: {data['phone']}\n"
             f"📍 Адрес: {message.text}\n"
             f"🛍 Товары: {len(cart)} шт.\n"
             f"💰 Сумма: {total} ₽",
        parse_mode='Markdown'
    )
    
    await state.finish()
    await message.answer(
        '✅ Заказ оформлен!\n'
        'Мы свяжемся с вами в ближайшее время.',
        reply_markup=main_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == 'clear_cart')
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    await callback.answer('🗑 Корзина очищена')
    await callback.message.edit_text('Корзина очищена')

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
