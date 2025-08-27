# bot.py
import os
import json
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

# === BOT ===
BOT_TOKEN = os.environ["BOT_TOKEN"]  # задається у Render -> Environment
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()
dp.include_router(router)

# === utils ===
def load_contacts() -> dict:
    """
    Читаємо дані з data.json (телефон, email, адрес).
    Якщо ключів немає — повертаємо N/A, щоб бот не падав.
    """
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    return {
        "phone": data.get("phone", "N/A"),
        "email": data.get("email", "N/A"),
        "address": data.get("address", "N/A"),
    }

def main_menu() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="🔁 Сменить язык")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# === handlers ===
@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать!\nНажмите «Контакты», чтобы получить контактную информацию.",
        reply_markup=main_menu(),
    )

@router.message(F.text == "📞 Контакты")
async def show_contacts(message: Message):
    c = load_contacts()
    text = (
        f"📱 Телефон: {c['phone']}\n"
        f"✉️ Email: {c['email']}\n"
        f"📍 Адрес: {c['address']}"
    )
    await message.answer(text, reply_markup=main_menu())

@router.message(F.text == "🔁 Сменить язык")
async def change_lang(message: Message):
    await message.answer("Пока доступен русский. Версия на ქართულ — в разработке 🙂")

# За замовчуванням на будь-який інший текст:
@router.message()
async def fallback(message: Message):
    await message.answer("Выберите пункт на клавиатуре ниже.", reply_markup=main_menu())
