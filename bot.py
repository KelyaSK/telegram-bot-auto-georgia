# -*- coding: utf-8 -*-
import os
import json
import logging
from pathlib import Path
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# Локально підхопимо .env, якщо є
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# -------- СЕКРЕТЫ ИЗ ОКРУЖЕНИЯ --------
BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_URL = (os.getenv("CHANNEL_URL") or "").strip()

if not BOT_TOKEN:
    raise SystemExit("❌ Не найден BOT_TOKEN. Укажите его в .env (локально) или в переменных окружения (на Render).")
if not CHANNEL_URL:
    logging.warning("⚠️ CHANNEL_URL не задан. Кнопка возврата использует https://t.me/")
    CHANNEL_URL = "https://t.me/"

# -------- ЛОГИ --------
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("bot")

# -------- ПУТИ И ДАННЫЕ --------
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data.json"

def load_contacts() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        title = data.get("title", "Контактная информация")
        items = data.get("items", [])
        return {"title": title, "items": items}
    except Exception as e:
        logger.exception(f"Не удалось прочитать {DATA_FILE}: {e}")
        return {"title": "Контактная информация", "items": []}

def render_contacts_text(data: dict) -> str:
    lines = [f"<b>{data.get('title','Контактная информация')}</b>", ""]
    for item in data.get("items", []):
        name = item.get("name", "")
        value = item.get("value", "")
        url = item.get("url")
        if not name and not value:
            continue
        if url:
            lines.append(f"• <b>{name}:</b> <a href='{url}'>{value or url}</a>")
        else:
            if name.lower().startswith("тел") and value:
                lines.append(f"• <b>{name}:</b> <a href='tel:{value}'>{value}</a>")
            else:
                lines.append(f"• <b>{name}:</b> {value}")
    return "\n".join(lines)

# -------- КЛАВИАТУРЫ --------
def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📞 Контакты"))
    kb.add(KeyboardButton("↩️ Назад в канал"))
    return kb

def back_inline_kb(url: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Вернуться в канал", url=url))
    return kb

# -------- ХЕНДЛЕРЫ (aiogram 3) --------
dp = Dispatcher()

@dp.message(CommandStart())
async def on_start(message: Message):
    text = (
        "Добро пожаловать в наш канал!\n"
        "Нажмите кнопку ниже, чтобы получить контактную информацию 👇"
    )
    await message.answer(text, reply_markup=main_menu())

# ловим любые варианты текста, где есть «контакт»
@dp.message(F.text.lower().contains("контакт"))
async def show_contacts(message: Message):
    data = load_contacts()
    await message.answer(
        render_contacts_text(data),
        reply_markup=main_menu(),
        disable_web_page_preview=True
    )

# ловим «назад»
@dp.message(F.text.lower().contains("назад"))
async def back_to_channel(message: Message):
    await message.answer(
        "🔙 Нажмите кнопку ниже, чтобы вернуться в канал:",
        reply_markup=back_inline_kb(CHANNEL_URL)
    )

# фолбек
@dp.message()
async def fallback(message: Message):
    await message.answer("Воспользуйтесь кнопками ниже 👇", reply_markup=main_menu())

# -------- ЗАПУСК --------
async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
