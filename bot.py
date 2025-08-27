import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 📂 Завантажуємо контакти з data.json
def load_contacts():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 📲 Головне меню
def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Оставить контакты")],
            [KeyboardButton(text="🌐 Сменить язык")]
        ],
        resize_keyboard=True
    )
    return kb

# 🖼 Привітання зі стартовою картинкою
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    try:
        with open("assets/Frame 81.png", "rb") as photo:
            await message.answer_photo(
                photo,
                caption="👋 Добро пожаловать!\nНажмите «📝 Оставить контакты» чтобы получить информацию.",
                reply_markup=main_menu()
            )
    except Exception as e:
        await message.answer("👋 Добро пожаловать!\n(Ошибка при загрузке изображения)", reply_markup=main_menu())

# 📞 Показати контакти
@dp.message(F.text == "📝 Оставить контакты")
async def show_contacts(message: Message):
    contacts = load_contacts()
    text = (
        f"📱 Телефон: {contacts.get('phone', '-')}\n"
        f"📧 Email: {contacts.get('email', '-')}\n"
        f"📍 Адрес: {contacts.get('address', '-')}"
    )
    await message.answer(text, reply_markup=main_menu())

# 🌐 Зміна мови (RU/KA)
@dp.message(F.text == "🌐 Сменить язык")
async def change_language(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇪 ქართული")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите язык:", reply_markup=kb)

# 🇷🇺 Вибір російської
@dp.message(F.text == "🇷🇺 Русский")
async def set_russian(message: Message):
    await message.answer("Язык переключен на русский.", reply_markup=main_menu())

# 🇬🇪 Вибір грузинської
@dp.message(F.text == "🇬🇪 ქართული")
async def set_georgian(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 კონტაქტები")],
            [KeyboardButton(text="🌐 ენის შეცვლა")]
        ],
        resize_keyboard=True
    )
    await message.answer("ენა შეიცვალა ქართულად.", reply_markup=kb)
