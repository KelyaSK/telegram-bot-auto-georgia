# -*- coding: utf-8 -*-
import os
import json
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# -------------------------------------------------------------------
# ВПИШИ СВОЇ ДАНІ НИЖЧЕ (залиш у лапках)
# -------------------------------------------------------------------
BOT_TOKEN   = "ВСТАВ_СВІЙ_ТОКЕН_З_BotFather"      # напр. 1234567890:AA... 
CHANNEL_URL = "https://t.me/your_channel_username" # напр. https://t.me/my_auto_channel
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data.json"

# ініціалізація бота
if not BOT_TOKEN or BOT_TOKEN.strip() == "":
    raise SystemExit("Не заданий BOT_TOKEN у bot.py. Впиши свій токен у змінну BOT_TOKEN.")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# reply-клавіатура з двома кнопками
def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📞 Контакти"))
    kb.add(KeyboardButton("↩️ Назад в канал"))
    return kb

# inline-кнопка з переходом у канал
def back_inline_kb(url: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Повернутися в канал", url=url))
    return kb

# зчитування контактів із data.json щоразу (щоб можна було редагувати без перезапуску)
def load_contacts() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # очікуємо формат {"title": "...", "items": [ {name, value, url?}, ... ]}
        title = data.get("title", "Контактна інформація")
        items = data.get("items", [])
        return {"title": title, "items": items}
    except Exception as e:
        logging.exception(f"Помилка читання {DATA_FILE}: {e}")
        return {"title": "Контактна інформація", "items": []}

def render_contacts_text(data: dict) -> str:
    lines = [f"<b>{data['title']}</b>", ""]
    for it in data["items"]:
        name = it.get("name", "")
        value = it.get("value", "")
        url = it.get("url")
        if not name and not value:
            continue
        if url:
            lines.append(f"• <b>{name}:</b> <a href='{url}'>{value or url}</a>")
        else:
            # телефон у вигляді посилання tel: якщо схоже на номер
            if name.lower().startswith("тел") and value:
                lines.append(f"• <b>{name}:</b> <a href='tel:{value}'>{value}</a>")
            else:
                lines.append(f"• <b>{name}:</b> {value}")
    return "\n".join(lines)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    text = (
        "Добро пожаловать в наш канал!\n"
        "Нажмите кнопку ниже, чтобы получить контактную информацию 👇\n\n"
        "Або скористайтеся меню внизу."
    )
    await message.answer(text, reply_markup=main_menu())

@dp.message_handler(lambda m: (m.text or "").strip().lower() in ["контакти", "📞 контакти", "контакты", "📞 контакты"])
async def show_contacts(message: types.Message):
    data = load_contacts()
    await message.answer(render_contacts_text(data), reply_markup=main_menu(), disable_web_page_preview=True)

@dp.message_handler(lambda m: "назад" in (m.text or "").lower())
async def back_to_channel(message: types.Message):
    link = CHANNEL_URL.strip() or "https://t.me/"
    await message.answer("Натисніть кнопку нижче, щоб повернутися у канал:", reply_markup=back_inline_kb(link))

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Скористайтес
