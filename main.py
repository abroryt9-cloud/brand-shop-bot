import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8574715738:AAGrtvaU095ptjX-cgd9Da4EPKT4rgPz3Ng"
ADMIN_ID = 6660842028  # ТВОЙ ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---------- ТОВАРЫ ----------
products = {
    "shirt": {"name": "Рубашка Оксфорд", "price": 12900, "desc": "Египетский хлопок, классический крой"},
    "zip": {"name": "Зипка", "price": 9900, "desc": "Трикотаж, плотный"}
}

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, username TEXT, items TEXT,
        name TEXT, phone TEXT, address TEXT,
        total INTEGER, status TEXT, date TEXT
    )""")
    conn.commit()
    conn.close()
init_db()

# ---------- КОРЗИНА ----------
user_carts = {}

# ---------- СОСТОЯНИЯ ----------
class OrderForm(StatesGroup):
    name = State()
    phone = State()
    address = State()

# ---------- СТАРТ ----------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        "Это бот бренда Old Money.\n"
        "Команды:\n"
        "/catalog — каталог\n"
        "/cart — корзина\n"
        "/myorders — мои заказы"
    )

# ---------- КАТАЛОГ ----------
@dp.message(Command("catalog"))
async def cmd_catalog(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for pid, prod in products.items():
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{prod['name']} — {prod['price']} ₽",
                callback_data=f"product_{pid}"
            )
        ])
    await message.answer("🛍 Выберите товар:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("product_"))
async def show_product(call: CallbackQuery):
    pid = call.data.replace("product_", "")
    prod = products[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_{pid}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")]
    ])
    await call.message.edit_text(
        f"*{prod['name']}*\n\n{prod['desc']}\n\nЦена: {prod['price']} ₽",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data == "back_to_catalog")
async def back_to_catalog(call: CallbackQuery):
    await cmd_catalog(call.message)

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    uid = call.from_user.id
    pid = call.data.replace("add_", "")
    if uid not in user_carts:
        user_carts[uid] = []
    user_carts[uid].append(pid)
    await call.answer("✅ Добавлено в корзину")

# ---------- КОРЗИНА ----------
@dp.message(Command("cart"))
async def cmd_cart(message: Message):
    uid = message.from_user.id
    cart = user_carts.get(uid, [])
    if not cart:
        await message.answer("🛒 Корзина пуста")
        return
    total = 0
    text = "🛒 *Ваша корзина:*\n\n"
    for pid in cart:
        prod = products[pid]
        text += f"• {prod['name']} — {prod['price']} ₽\n"
        total += prod['price']
    text += f"\n*Итого: {total} ₽*"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: CallbackQuery):
    uid = call.from_user.id
    user_carts[uid] = []
    await call.answer("🗑 Корзина очищена")
    await cmd_cart(call.message)

# ---------- ОФОРМЛЕНИЕ ----------
@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    if not user_carts.get(uid):
        await call.answer("❌ Корзина пуста", show_alert=True)
        return
    await state.set_state(OrderForm.name)
    await call.message.answer("Введите ваше имя:")

@dp.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.phone)
    await message.answer("Введите номер телефона:")

@dp.message(OrderForm.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(OrderForm.address)
    await message.answer("Введите адрес доставки:")

@dp.message(OrderForm.address)
async def process_address(message: Message, state: FSMContext):
    uid = message.from_user.id
    data = await state.get_data()
    cart = user_carts.get(uid, [])
    total = sum(products[pid]['price'] for pid in cart)
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("""INSERT INTO orders 
        (user_id, username, items, name, phone, address, total, status, date)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (uid, message.from_user.username or "",
         ",".join(cart), data['name'], data['phone'],
         message.text, total, "новый", datetime.now().isoformat()))
    conn.commit()
    order_id = c.lastrowid
    conn.close()
    user_carts[uid] = []
    await state.clear()
    await bot.send_message(
        ADMIN_ID,
        f"📦 *НОВЫЙ ЗАКАЗ #{order_id}*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📍 Адрес: {message.text}\n"
        f"🛍 Товаров: {len(cart)}\n"
        f"💰 Сумма: {total} ₽",
        parse_mode="Markdown"
    )
    await message.answer("✅ Заказ оформлен! Мы свяжемся с вами.")

# ---------- МОИ ЗАКАЗЫ ----------
@dp.message(Command("myorders"))
async def cmd_myorders(message: Message):
    uid = message.from_user.id
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("SELECT id, total, status, date FROM orders WHERE user_id=? ORDER BY date DESC LIMIT 5", (uid,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await message.answer("📦 У вас ещё нет заказов")
        return
    text = "📦 *Ваши последние заказы:*\n\n"
    for r in rows:
        text += f"• Заказ #{r[0]} — {r[1]} ₽ ({r[2]})\n"
    await message.answer(text, parse_mode="Markdown")

# ---------- ЗАПУСК ----------
async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
