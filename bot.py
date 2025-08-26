# -*- coding: utf-8 -*-
import os
import json
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Локально подхватим .env, если библиотека установлена (python-dotenv в requirements)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# -------- СЕКРЕТЫ ИЗ ОКРУЖЕНИЯ --------
BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL", "").strip()

if not BOT_TOKEN:
    raise SystemExit("❌ Не найден BOT_TOKEN. Укажите его в .env (локально) или в переменных окружения (на Render).")

if not CHANNEL_URL:
    logging.warning("⚠️ CHANNEL_URL не задан. Кнопка возврата использует https://t.me/")
    CHANNEL_URL = "https://t.me/"

# -------- ЛОГИ --------
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("bot")

# -------- ПУТИ --------
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data.json"

# -------- ИНИЦИАЛИЗАЦИЯ --------
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

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

# -------- РАБОТА С data.json --------
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
            # Если это телефон, сделаем кликабельным tel:
            if name.lower().startswith("тел") and value:
                lines.append(f"• <b>{name}:</b> <a href='tel:{value}'>{value}</a>")
            else:
                lines.append(f"• <b>{name}:</b> {value}")
    return "\n".join(lines)

# -------- ХЕНДЛЕРЫ --------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    text = (
        "Добро пожаловать в наш канал!\n"
        "Нажмите кнопку ниже, чтобы получить контактную информацию 👇"
    )
    await message.answer(text, reply_markup=main_menu())

# Ловим любые варианты текста с «контакт»
@dp.message_handler(lambda m: m.text and "контакт" in m.text.lower())
async def show_contacts(message: types.Message):
    data = load_contacts()
    await message.answer(render_contacts_text(data), reply_markup=main_menu(), disable_web_page_preview=True)

# Ловим «назад»
@dp.message_handler(lambda m: m.text and "назад" in m.text.lower())
async def back_to_channel(message: types.Message):
    await message.answer("🔙 Нажмите кнопку ниже, чтобы вернуться в канал:", reply_markup=back_inline_kb(CHANNEL_URL))

# Фолбек
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Воспользуйтесь кнопками ниже 👇", reply_markup=main_menu())

# -------- ЗАПУСК --------
if __name__ == "__main__":
    logger.info("✅ Бот запущен (polling)…")
    executor.start_polling(dp, skip_updates=True)
