# bot.py
import json, os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()
dp.include_router(router)

def load_contacts():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def main_menu():
    kb = [
        [KeyboardButton(text="📞 Контакти")],
        [KeyboardButton(text="🌐 Змінити мову")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать!\nНажмите кнопку ниже, чтобы получить контакты:",
        reply_markup=main_menu()
    )

@router.message(F.text == "📞 Контакти")
async def show_contacts(message: Message):
    data = load_contacts()
    text = (
        f"📱 Телефон: {data.get('phone','N/A')}\n"
        f"📧 Email: {data.get('email','N/A')}\n"
        f"📍 Адрес: {data.get('address','N/A')}"
    )
    await message.answer(text, reply_markup=main_menu())

@router.message(F.text == "🌐 Змінити мову")
async def change_lang(message: Message):
    await message.answer("Поки доступні 🇷🇺 Русский та 🇬🇪 ქართული (у розробці).")
