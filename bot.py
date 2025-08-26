# -*- coding: utf-8 -*-
import json
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ---------------------------
# ТВОЇ СЕКРЕТИ (підставлено прямо в код)
# ---------------------------
BOT_TOKEN = "ТУТ_ТВІЙ_ТОКЕН_ВІД_BOTFATHER"
CHANNEL_URL = "https://t.me/your_channel_username"

# ---------------------------
# Налаштування
# ---------------------------
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

DATA_FILE = Path(__file__).parent / "data.json"

def load_contacts():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📞 Контакти"))
    kb.add(KeyboardButton("↩️ Назад в канал"))
    return kb

def back_inline_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Повернутися в канал", url=CHANNEL_URL))
    return kb

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    text = (
        "Добро пожаловать в наш канал!\n"
        "Нажмите кнопку ниже, чтобы получить контактную информацию 👇"
    )
    await message.answer(text, reply_markup=main_menu())

@dp.message_handler(lambda m: "контакти" in m.text.lower())
async def show_contacts(message: types.Message):
    data = load_contacts()
    text = "<b>📞 Контактна інформація</b>\n\n"
    for item in data.get("items", []):
        name, value = item.get("name"), item.get("value")
        url = item.get("url")
        if url:
            text += f"• <b>{name}:</b> <a href='{url}'>{value}</a>\n"
        else:
            text += f"• <b>{name}:</b> {value}\n"
    await message.answer(text, reply_markup=main_menu(), disable_web_page_preview=True)

@dp.message_handler(lambda m: "назад" in m.text.lower())
async def back_to_channel(message: types.Message):
    await message.answer("Натисніть кнопку нижче, щоб повернутися у канал:", reply_markup=back_inline_kb())

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Скористайтеся кнопками внизу 👇", reply_markup=main_menu())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
