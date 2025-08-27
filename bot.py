# bot.py
import json
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# --- Кнопки / клавіатура ---
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
    """
    Читає контакти з data.json, який лежить поряд із bot.py.
    Повертає словник зі значеннями або дефолтні «—» у разі помилки.
    """
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

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Я телеграм-бот.\n\n"
        "Выберите пункт на клавиатуре ниже 👇"
    )
    await message.answer(text, reply_markup=MAIN_KB)

@router.message(F.text == "📞 Контакты")
async def contacts(message: Message) -> None:
    info = read_contacts()
    text = (
        "📞 Контакты:\n"
        f"• Телефон: {info['phone']}\n"
        f"• Email: {info['email']}\n"
        f"• Адрес: {info['address']}"
    )
    await message.answer(text, reply_markup=MAIN_KB)

@router.message(F.text == "🔁 Сменить язык")
async def change_lang(message: Message) -> None:
    await message.answer(
        "Пока доступен русский. Версия на ქართულ — в разработке 🙂",
        reply_markup=MAIN_KB,
    )

@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Выберите пункт на клавиатуре ниже", reply_markup=MAIN_KB)
