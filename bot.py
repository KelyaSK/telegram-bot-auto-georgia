# bot.py
import json
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# --- Клавіатура ---
MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="🔁 Сменить язык")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт...",
)

# Експортуємо роутер — його підхоплює server.py
router = Router()

def read_contacts() -> dict:
    """Читає контакти з data.json поруч із файлом."""
    data_path = Path(__file__).parent / "data.json"
    try:
        with data_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("data.json must contain a JSON object")
            return {
                "phone": data.get("phone", "—"),
                "email": data.get("email", "—"),
                "address": data.get("address", "—"),
            }
    except Exception:
        return {"phone": "—", "email": "—", "address": "—"}

@router.message(Command("ping"))
async def ping(message: Message):
    await message.answer("pong")

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я телеграм-бот.\n\nВыберите пункт на клавиатуре ниже 👇",
        reply_markup=MAIN_KB,
    )

@router.message(F.text == "📞 Контакты")
async def contacts(message: Message):
    info = read_contacts()
    await message.answer(
        "📞 Контакты:\n"
        f"• Телефон: {info['phone']}\n"
        f"• Email: {info['email']}\n"
        f"• Адрес: {info['address']}",
        reply_markup=MAIN_KB,
    )

@router.message(F.text == "🔁 Сменить язык")
async def change_lang(message: Message):
    await message.answer(
        "Пока доступен русский. Версия на ქართულ — в разработке 🙂",
        reply_markup=MAIN_KB,
    )

@router.message()
async def fallback(message: Message):
    await message.answer("Выберите пункт на клавиатуре ниже", reply_markup=MAIN_KB)
