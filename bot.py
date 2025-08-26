# -*- coding: utf-8 -*-
import os
import json
import logging
from pathlib import Path
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    LinkPreviewOptions
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# -------- СЕКРЕТЫ --------
BOT_TOKEN     = os.getenv("BOT_TOKEN")
CHANNEL_URL   = (os.getenv("CHANNEL_URL") or "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

ADMINS_ENV = (os.getenv("ADMINS") or "").strip()
ADMINS = {int(x) for x in ADMINS_ENV.split(",") if x.strip().isdigit()}

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN не найден")

if not CHANNEL_URL:
    CHANNEL_URL = "https://t.me/"

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("bot")

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data.json"

USER_LANG: dict[int, str] = {}  # user_id -> 'ru'|'ka'

T = {
    "ru": {
        "welcome": "Добро пожаловать в наш канал!\nНажмите кнопку ниже, чтобы получить контактную информацию 👇",
        "use_buttons": "Выберите действие ниже 👇",
        "back_prompt": "🔙 Нажмите кнопку ниже, чтобы вернуться в канал:",
        "thanks_contact": "Спасибо! Мы свяжемся с вами по номеру: <b>{phone}</b>",
        "reload_ok": "Данные перезагружены ✅",
        "no_perm": "Недостаточно прав.",
        "lang_pick": "Выберите язык:",
        "set_lang_ok": "Язык переключен на: Русский 🇷🇺",
        "set_lang_ok_ka": "Язык переключен на: Грузинский 🇬🇪",
        # кнопки
        "btn_contacts": "📞 Контакты",
        "btn_leave_number": "📲 Оставить номер",
        "btn_back_to_channel": "↩️ Назад в канал",
        "btn_language": "🌐 Язык / ენა",
        "btn_back_inline": "🔙 Вернуться в канал",
    },
    "ka": {
        "welcome": "მოგესალმებით ჩვენს არხში!\nქვემოთ მდებარე ღილაკზე დააჭირეთ, რათა მიიღოთ საკონტაქტო ინფორმაცია 👇",
        "use_buttons": "აირჩიეთ ქმედება ქვემოთ 👇",
        "back_prompt": "🔙 არხში დასაბრუნებლად დააჭირეთ ქვემოთ მოცემულ ღილაკს:",
        "thanks_contact": "გმადლობთ! ჩვენ დაგიკავშირდებით ნომერზე: <b>{phone}</b>",
        "reload_ok": "მონაცემები განახლდა ✅",
        "no_perm": "წვდომა აკრძალულია.",
        "lang_pick": "აირჩიეთ ენა:",
        "set_lang_ok": "ენა შეიცვალა: ქართული 🇬🇪",
        "set_lang_ok_ka": "ენა შეიცვალა: ქართული 🇬🇪",
        # кнопки
        "btn_contacts": "📞 კონტაქტები",
        "btn_leave_number": "📲 ნომრის გაგზავნა",
        "btn_back_to_channel": "↩️ არხში დაბრუნება",
        "btn_language": "🌐 Язык / ენა",
        "btn_back_inline": "🔙 არხში დაბრუნება",
    },
}

def get_lang(user_id: int) -> str:
    return USER_LANG.get(user_id, "ru")

def set_lang(user_id: int, lang: str):
    USER_LANG[user_id] = lang if lang in ("ru", "ka") else "ru"

def load_contacts() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("bad format")
        if "items" not in data or not isinstance(data["items"], list):
            data["items"] = []
        if "title" not in data or not isinstance(data["title"], str):
            data["title"] = "Контактная информация"
        return data
    except Exception as e:
        logger.exception(f"Ошибка чтения {DATA_FILE}: {e}")
        return {"title": "Контактная информация", "items": []}

def render_contacts_text(data: dict) -> str:
    lines = [f"<b>{data.get('title','Контактная информация')}</b>", ""]
    for item in data.get("items", []):
        name = str(item.get("name", "")).strip()
        value = str(item.get("value", "")).strip()
        url = str(item.get("url", "")).strip() if item.get("url") else ""
        if not name and not value:
            continue
        if url:
            lines.append(f"• <b>{name}:</b> <a href='{url}'>{value or url}</a>")
        else:
            lines.append(f"• <b>{name}:</b> {value}")
    return "\n".join(lines)

def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=T[lang]["btn_contacts"])],
            [KeyboardButton(text=T[lang]["btn_leave_number"], request_contact=True)],
            [KeyboardButton(text=T[lang]["btn_back_to_channel"])],
            [KeyboardButton(text=T[lang]["btn_language"])],
        ],
        resize_keyboard=True
    )

def back_inline_kb(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=T[lang]["btn_back_inline"], url=url)]
        ]
    )

def language_picker_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский 🇷🇺", callback_data="setlang:ru"),
                InlineKeyboardButton(text="ქართული 🇬🇪", callback_data="setlang:ka"),
            ]
        ]
    )

dp = Dispatcher()

@dp.message(CommandStart())
async def on_start(message: Message):
    if message.from_user.id not in USER_LANG:
        set_lang(message.from_user.id, "ru")
    lang = get_lang(message.from_user.id)
    await message.answer(T[lang]["welcome"], reply_markup=main_menu(lang))

@dp.message(F.text.casefold().contains("контакт") | F.text.casefold().contains("კონტაქტ"))
async def show_contacts(message: Message):
    lang = get_lang(message.from_user.id)
    data = load_contacts()
    await message.answer(
        render_contacts_text(data),
        reply_markup=main_menu(lang),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

@dp.message(F.text.casefold().contains("назад") | F.text.casefold().contains("არხში დაბრუნ"))
async def back_to_channel(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(
        T[lang]["back_prompt"],
        reply_markup=back_inline_kb(lang, CHANNEL_URL)
    )

@dp.message(F.text.casefold().contains("язык") | F.text.casefold().contains("ენა"))
async def choose_language(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(T[lang]["lang_pick"], reply_markup=language_picker_kb())

@dp.callback_query(F.data.startswith("setlang:"))
async def set_language(cb: CallbackQuery):
    target = cb.data.split(":", 1)[1]
    set_lang(cb.from_user.id, target)
    if target == "ru":
        await cb.message.edit_text(T["ru"]["set_lang_ok"])
        await cb.message.answer(T["ru"]["use_buttons"], reply_markup=main_menu("ru"))
    else:
        await cb.message.edit_text(T["ka"]["set_lang_ok"])
        await cb.message.answer(T["ka"]["use_buttons"], reply_markup=main_menu("ka"))
    await cb.answer()

@dp.message(F.contact)
async def got_contact(message: Message):
    lang = get_lang(message.from_user.id)
    phone = message.contact.phone_number
    name = message.contact.first_name or ""
    await message.answer(T[lang]["thanks_contact"].format(phone=phone))
    if ADMIN_CHAT_ID and ADMIN_CHAT_ID.strip("-").isdigit():
        try:
            await message.bot.send_message(
                int(ADMIN_CHAT_ID),
                f"📲 Новый контакт:\nИмя: {name}\nТелефон: {phone}\nUser: @{message.from_user.username or '-'} (id={message.from_user.id})"
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить контакт админу: {e}")

@dp.message(F.text == "/reload")
async def reload_data(message: Message):
    if message.from_user.id not in ADMINS:
        lang = get_lang(message.from_user.id)
        await message.answer(T[lang]["no_perm"])
        return
    _ = load_contacts()
    lang = get_lang(message.from_user.id)
    await message.answer(T[lang]["reload_ok"])

@dp.message()
async def fallback(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(T[lang]["use_buttons"], reply_markup=main_menu(lang))

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())
