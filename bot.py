import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# Завантажуємо змінні з .env
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/your_channel")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ---------------- Меню ---------------- #
def main_menu(lang="ru"):
    kb = ReplyKeyboardBuilder()
    if lang == "ru":
        kb.button(text="📞 Контакты")
        kb.button(text="🔙 Назад в канал")
    elif lang == "ka":
        kb.button(text="📞 კონტაქტები")
        kb.button(text="🔙 არხზე დაბრუნება")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def back_inline_kb(channel_url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в канал", url=channel_url)]
        ]
    )

# ---------------- Завантаження контактів ---------------- #
def load_contacts():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------- Стартове повідомлення ---------------- #
@dp.message(Command("start"))
async def start_cmd(message: Message):
    caption = (
        "👋 Добро пожаловать!\n"
        "Нажмите «/start» и получите контакты и помощь по авто 🚘"
    )

    local_path = "assets/Frame81.png"
    backup_url = "https://i.imgur.com/3ZQ3ZyK.png"  # 👉 заміни на свою URL-картинку

    try:
        if os.path.exists(local_path):
            with open(local_path, "rb") as photo:
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=main_menu("ru")
                )
        else:
            await message.answer_photo(
                photo=backup_url,
                caption=caption,
                reply_markup=main_menu("ru")
            )
    except Exception as e:
        await message.answer("⚠️ Ошибка при загрузке изображения")
        print(f"Image error: {e}")

# ---------------- Кнопки ---------------- #
@dp.message(F.text.in_(["📞 Контакты", "📞 კონტაქტები"]))
async def show_contacts(message: Message):
    contacts = load_contacts()
    text = (
        f"<b>📞 Телефон:</b> {contacts['phone']}\n"
        f"<b>✉️ Email:</b> {contacts['email']}\n"
        f"<b>📍 Адрес:</b> {contacts['address']}"
    )
    await message.answer(text, reply_markup=main_menu("ru"))

@dp.message(F.text.in_(["🔙 Назад в канал", "🔙 არხზე დაბრუნება"]))
async def back_to_channel(message: Message):
    await message.answer(
        "🔙 Вернитесь в канал по кнопке ниже:",
        reply_markup=back_inline_kb(CHANNEL_URL)
    )

# ---------------- Запуск ---------------- #
if __name__ == "__main__":
    import asyncio
    print("🤖 Бот запущен...")
    asyncio.run(dp.start_polling(bot))
