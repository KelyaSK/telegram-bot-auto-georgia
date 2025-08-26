import os
import json
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ---------- НАЛАШТУВАННЯ ----------
# РЕКОМЕНДОВАНО: взяти з ENV (Render)
API_TOKEN = os.getenv("BOT_TOKEN", "7583570411:AAF3hU0M0f1o0YR4ywQa68S_U-q8LAdkCL4")
# fallback на data.json -> channel_link; це лиш резерв:
CHANNEL_URL_ENV = os.getenv("CHANNEL_URL", "")

# (необов'язково) Admin ID для /set_* команд
ADMIN_ID = os.getenv("ADMIN_ID")  # числовий Telegram ID
ADMINS = {int(ADMIN_ID)} if ADMIN_ID and ADMIN_ID.isdigit() else set()

# ---------- ЛОГУВАННЯ ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- ДАНІ ----------
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Не вдалось прочитати data.json")
        return {
            "channel_link": "https://t.me/YourChannel",
            "contacts": {"phone": "-", "email": "-", "address": "-"}
        }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ---------- БОТ ----------
if not API_TOKEN:
    logger.error("ENV BOT_TOKEN не встановлено")
    raise SystemExit(1)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📞 Контакти"))
    kb.add(KeyboardButton("↩️ Назад в канал"))
    return kb

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply(
        "Виберіть дію 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "📞 Контакти")
async def show_contacts(message: types.Message):
    data = load_data()
    c = data.get("contacts", {})
    phone = c.get("phone", "—")
    email = c.get("email", "—")
    address = c.get("address", "—")

    text = (
        f"<b>📞 Контактна інформація</b>\n\n"
        f"📱 Телефон: <a href='tel:{phone}'>{phone}</a>\n"
        f"📧 Email: <a href='mailto:{email}'>{email}</a>\n"
        f"📍 Адреса: {address}"
    )
    await message.answer(text, disable_web_page_preview=True)

@dp.message_handler(lambda m: m.text == "↩️ Назад в канал")
async def back_to_channel(message: types.Message):
    data = load_data()
    link = data.get("channel_link") or CHANNEL_URL_ENV or "https://t.me/YourChannel"
    await message.answer(f"🔗 Перейти в канал: {link}")

# ------ Адмін-команди (необов'язково) ------
def is_admin(uid: int) -> bool:
    return uid in ADMINS if ADMINS else False

@dp.message_handler(commands=["set_phone"])
async def set_phone(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("⛔ У вас немає прав.")
    try:
        new = message.text.split(" ", 1)[1].strip()
    except IndexError:
        return await message.reply("⚠️ Використання: /set_phone +995555123456")
    data = load_data()
    data["contacts"]["phone"] = new
    save_data(data)
    await message.reply(f"✅ Телефон оновлено: {new}")

@dp.message_handler(commands=["set_email"])
async def set_email(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("⛔ У вас немає прав.")
    try:
        new = message.text.split(" ", 1)[1].strip()
    except IndexError:
        return await message.reply("⚠️ Використання: /set_email name@mail.com")
    data = load_data()
    data["contacts"]["email"] = new
    save_data(data)
    await message.reply(f"✅ Email оновлено: {new}")

@dp.message_handler(commands=["set_address"])
async def set_address(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("⛔ У вас немає прав.")
    try:
        new = message.text.split(" ", 1)[1].strip()
    except IndexError:
        return await message.reply("⚠️ Використання: /set_address Місто, вулиця 1")
    data = load_data()
    data["contacts"]["address"] = new
    save_data(data)
    await message.reply(f"✅ Адресу оновлено: {new}")

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    logger.info("Бот запущено локально...")
    executor.start_polling(dp, skip_updates=True)
