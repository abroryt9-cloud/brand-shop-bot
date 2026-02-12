import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
from datetime import datetime
from flask import Flask
import threading

# Flask-заглушка для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Запуск Flask в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

# Токен и ID
TOKEN = '8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng'
ADMIN_ID =6660842028 # ТВОЙ ID

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Товары
products = {
    'shirt': {'name': 'Классическая рубашка', 'price': 11000, 'desc': 'Премиум-рубашка Old Money'},
    'zip': {'name': 'Олимпийка', 'price': 9900, 'desc': 'Трикотаж Old Money'}
}

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

# Состояния заказа
class OrderForm(StatesGroup):
    name = State()
    phone = State()
    address = State()

# Корзина (в памяти)
user_carts = {}

# Команда /start
@dp.message(Command('start'))
async def start_cmd(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛍 Каталог', callback_data='catalog')],
        [InlineKeyboardButton(text='🛒 Корзина', callback_data='cart'),
         InlineKeyboardButton(text='📦 Мои заказы', callback_data='my_orders')]
    ])
    await message.answer(
        f'👋 Привет, {message.from_user.first_name}!\n'
        'Это бот бренда [НАЗВАНИЕ]. Здесь можно заказать премиум-одежду.',
        reply_markup=keyboard
    )

# Каталог
@dp.callback_query(lambda c: c.data == 'catalog')
async def catalog(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for pid, prod in products.items():
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{prod['name']} — {prod['price']} ₽",
                callback_data=f'product_{pid}'
            )
        ])
    await callback.message.edit_text('Выберите товар:', reply_markup=keyboard)

# Товар
@dp.callback_query(lambda c: c.data.startswith('product_'))
async def show_product(callback: types.CallbackQuery):
    pid = callback.data.replace('product_', '')
    prod = products[pid]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛒 Добавить в корзину', callback_data=f'add_{pid}')],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='catalog')]
    ])
    
    await callback.message.edit_text(
        f"*{prod['name']}*\n\n"
        f"{prod['desc']}\n\n"
        f"Цена: {prod['price']} ₽",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Добавить в корзину
@dp.callback_query(lambda c: c.data.startswith('add_'))
async def add_to_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pid = callback.data.replace('add_', '')
    
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    user_carts[user_id].append(pid)
    await callback.answer('✅ Товар добавлен в корзину')
    await catalog(callback)

# Корзина
@dp.callback_query(lambda c: c.data == 'cart')
async def show_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        await callback.message.edit_text('🛒 Корзина пуста')
        return
    
    total = 0
    text = '🛒 *Ваша корзина:*\n\n'
    for pid in cart:
        prod = products[pid]
        text += f"• {prod['name']} — {prod['price']} ₽\n"
        total += prod['price']
    
    text += f'\n*Итого: {total} ₽*'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Оформить заказ', callback_data='checkout')],
        [InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart')],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='start')]
    ])
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)

# Очистить корзину
@dp.callback_query(lambda c: c.data == 'clear_cart')
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    await callback.answer('🗑 Корзина очищена')
    await show_cart(callback)

# Оформление заказа
@dp.callback_query(lambda c: c.data == 'checkout')
async def checkout(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not user_carts.get(user_id):
        await callback.answer('❌ Корзина пуста')
        return
    
    await state.set_state(OrderForm.name)
    await callback.message.edit_text('Введите ваше имя:')

@dp.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.phone)
    await message.answer('Введите номер телефона:')

@dp.message(OrderForm.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(OrderForm.address)
    await message.answer('Введите адрес доставки:')

@dp.message(OrderForm.address)
async def process_address(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    cart = user_carts.get(user_id, [])
    
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
    
    # Отправляем уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"📦 *НОВЫЙ ЗАКАЗ #{order_id}*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📍 Адрес: {message.text}\n"
        f"🛍 Товары: {len(cart)} шт.\n"
        f"💰 Сумма: {total} ₽",
        parse_mode='Markdown'
    )
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛍 В каталог', callback_data='catalog')]
    ])
    
    await message.answer(
        '✅ Заказ оформлен!\n'
        'Мы свяжемся с вами в ближайшее время.',
        reply_markup=keyboard
    )

# Мои заказы
@dp.callback_query(lambda c: c.data == 'my_orders')
async def my_orders(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT id, total, status, date FROM orders WHERE user_id=? ORDER BY date DESC LIMIT 5', (user_id,))
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        await callback.message.edit_text('📦 У вас пока нет заказов')
        return
    
    text = '📦 *Ваши последние заказы:*\n\n'
    for order in orders:
        status_emoji = '✅' if order[2] == 'новый' else '🔄'
        text += f"{status_emoji} Заказ #{order[0]} — {order[1]} ₽ ({order[3][:10]})\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='start')]
    ])
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
