import os
import json
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ===== НАЛАШТУВАННЯ =====
# РЕКОМЕНДОВАНО: зчитувати токен з ENV (щоб не світився у коді).
# Якщо ENV немає — використовуємо ваш поточний токен як запасний варіант.
API_TOKEN = os.getenv("BOT_TOKEN", "7583570411:AAF3hU0M0f1o0YR4ywQa68S_U-q8LAdkCL4")

# Посилання на канал: беремо з data.json, але також дозволяємо ENV як запасний варіант
CHANNEL_URL_ENV = os.getenv("CHANNEL_URL", "")

# ===== ЛОГУВАННЯ =====
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("bot")

# ===== ШЛЯХ ДО data.json (надійний абсолютний) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

def load_data():
    """Читає data.json і повертає словник. Якщо є помилка — повертає дефолтні значення."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Базова перевірка структури
        if "contacts" not in data or not isinstance(data["contacts"], dict):
            raise ValueError("У data.json немає об'єкта 'contacts'")
        return data
    except Exception as e:
        logger.exception(f"Помилка читання {DATA_FILE}: {e}")
        return {
            "channel_link": "https://t.me/YourChannel",
            "contacts": {"phone": "—", "email": "—", "address": "—"}
        }

# ===== ІНІЦІАЛІЗАЦІЯ БОТА =====
if not API_TOKEN:
    raise SystemExit("ENV BOT_TOKEN не встановлено")

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== КЛАВІАТУРА З КНОПКАМИ =====
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📞 Контакти"))
    kb.add(KeyboardButton("↩️ Назад в канал"))
    return kb

# ===== ХЕНДЛЕРИ =====
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("Виберіть дію 👇", reply_markup=main_menu())

@dp.message_handler(lambda m: (m.text or "").strip() in ["📞 Контакти", "Контакти", "Контакты", "📞 Контакты"])
async def show_contacts(message: types.Message):
    data = load_data()
    c = data.get("contacts", {})
    phone = c.get("phone", "—")
    email = c.get("email", "—")
    address = c.get("address", "—")

    text = (
        "<b>📞 Контактна інформація</b>\n\n"
        f"📱 Телефон: <a href='tel:{phone}'>{phone}</a>\n"
        f"📧 Email: <a href='mailto:{email}'>{email}</a>\n"
        f"📍 Адреса: {address}"
    )
    await message.answer(text, disable_web_page_preview=True)

@dp.message_handler(lambda m: (m.text or "").strip() == "↩️ Назад в канал")
async def back_to_channel(message: types.Message):
    data = load_data()
    link = data.get("channel_link") or CHANNEL_URL_ENV or "https://t.me/YourChannel"
    await message.answer(f"🔗 Перейти в канал: {link}")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    logger.info(f"Запуск бота... DATA_FILE = {DATA_FILE}")
    executor.start_polling(dp, skip_updates=True)
