# -*- coding: utf-8 -*-
import json
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# -------------------------------------------------------------------
# ВСТАВ СВОЇ ДАНІ
# -------------------------------------------------------------------
BOT_TOKEN   = "ВСТАВ_СВІЙ_ТОКЕН"         # токен від BotFather
CHANNEL_URL = "https://t.me/your_channel" # посилання на твій канал
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("bot")

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data.json"

# ініціалізація
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ---------------- Клавіатури ----------------
def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📞 Контакти"))
    kb.add(KeyboardButton("↩️ Назад в канал"))
    return kb

def back_inline_kb(url: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Повернутися в канал", url=url))
    return kb

# ---------------- Робота з data.json ----------------
def load_contacts() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception(f"Не вдалося прочитати {DATA_FILE}: {e}")
        return {"title": "Контактна інформація", "items": []}

def render_contacts_text(data: dict) -> str:
    lines = [f"<b>{data.get('title','Контактна інформація')}</b>", ""]
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

# ---------------- Хендлери ----------------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    text = (
        "Добро пожаловать в наш канал!\n"
        "Нажмите кнопку ниже, чтобы получить контактную информацию 👇"
    )
    await message.answer(text, reply_markup=main_menu())

@dp.message_handler(lambda m: m.text and "контакт" in m.text.lower())
async def show_contacts(message: types.Message):
    data = load_contacts()
    await message.answer(render_contacts_text(data), reply_markup=main_menu(), disable_web_page_preview=True)

@dp.message_handler(lambda m: m.text and "назад" in m.text.lower())
async def back_to_channel(message: types.Message):
    await message.answer("Натисніть кнопку нижче, щоб повернутися у канал:", reply_markup=back_inline_kb(CHANNEL_URL))

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Скористайтеся кнопками внизу 👇", reply_markup=main_menu())

# ---------------- Запуск ----------------
if __name__ == "__main__":
    logger.info("Бот запущений…")
    executor.start_polling(dp, skip_updates=True)
