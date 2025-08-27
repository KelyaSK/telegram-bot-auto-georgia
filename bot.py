# bot.py
import json
import os
from pathlib import Path
from typing import Dict, Any

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

# ====== Константи / ENV ======
BASE_DIR = Path(__file__).parent
BANNER_PATH = BASE_DIR / "assets" / "banner.png"
DATA_JSON = BASE_DIR / "data.json"
CHANNEL_URL = os.getenv("CHANNEL_URL")  # наприклад: https://t.me/your_channel

# Внутрішній «стан» мови користувача (пам’ять у RAM; після рестарту збивається)
# RU за замовчуванням; 'ru' або 'ka'
USER_LANG: Dict[int, str] = {}

# ====== Тексти RU/KA ======
TXT = {
    "ru": {
        "start_caption": "👋 Добро пожаловать!\nНажмите «/start» и получите контакты и помощь по авто 🚗",
        "menu_contacts": "📞 Контакты",
        "menu_lang": "🔁 Сменить язык",
        "menu_back_channel": "🔙 Назад в канал",
        "contacts_title": "📞 Контакты:",
        "contacts_phone": "Телефон",
        "contacts_email": "Email",
        "contacts_addr": "Адрес",
        "lang_switched": "Язык переключен на ქართული.",
        "open_channel": "Открыть канал",
        "no_channel": "Ссылка на канал не настроена.",
        "catalog_empty": "Каталог временно пуст.",
        "ignored": "",  # нічого не шлемо
    },
    "ka": {
        "start_caption": "👋 მოგესალმებით!\nდააჭირეთ «/start» და მიიღეთ კონტაქტები და დახმარება ავტომობილებზე 🚗",
        "menu_contacts": "📞 კონტაქტები",
        "menu_lang": "🔁 ენის შეცვლა",
        "menu_back_channel": "🔙 არხზე დაბრუნება",
        "contacts_title": "📞 კონტაქტები:",
        "contacts_phone": "ტელეფონი",
        "contacts_email": "იმეილი",
        "contacts_addr": "მისამართი",
        "lang_switched": "ენა შეიცვალა რუსულზე.",
        "open_channel": "არხის გახსნა",
        "no_channel": "არხის ბმული არ არის მითითებული.",
        "catalog_empty": "კატალოგი დროებით ცარიელია.",
        "ignored": "",
    },
}

# Для матчів тексту кнопок приймемо обидві мови
LABELS = {
    "contacts": {"ru": "📞 Контакты", "ka": "📞 კონტაქტები"},
    "lang": {"ru": "🔁 Сменить язык", "ka": "🔁 ენის შეცვლა"},
    "back_channel": {"ru": "🔙 Назад в канал", "ka": "🔙 არხზე დაბრუნება"},
}

def lang_of(user_id: int) -> str:
    """Повертає поточну мову користувача ('ru'|'ka'). За замовчуванням RU."""
    return USER_LANG.get(user_id, "ru")

def toggle_lang(user_id: int) -> str:
    new_lang = "ka" if lang_of(user_id) == "ru" else "ru"
    USER_LANG[user_id] = new_lang
    return new_lang

def read_contacts() -> Dict[str, Any]:
    try:
        data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        return {
            "phone": data.get("phone", "—"),
            "email": data.get("email", "—"),
            "address": data.get("address", "—"),
        }
    except Exception:
        return {"phone": "—", "email": "—", "address": "—"}

def make_main_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LABELS["contacts"][lang])],
            [KeyboardButton(text=LABELS["lang"][lang])],
            [KeyboardButton(text=LABELS["back_channel"][lang])],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт..." if lang == "ru" else "აირჩიეთ პუნქტი...",
    )

router = Router()

# ====== Хендлери ======

@router.message(CommandStart())
async def on_start(message: Message):
    uid = message.from_user.id
    # Мова за замовчуванням RU (не міняємо, поки юзер не натисне «Сменить язык»)
    current = lang_of(uid)
    kb = make_main_kb(current)

    # 1) Надсилаємо банер (якщо є)
    if BANNER_PATH.exists():
        await message.answer_photo(
            photo=BANNER_PATH.open("rb"),
            caption=TXT[current]["start_caption"]
        )
    else:
        await message.answer(TXT[current]["start_caption"])

    # 2) Показуємо клавіатуру (прикріплена знизу)
    await message.answer(" ", reply_markup=kb)

@router.message(Command("ping"))
async def on_ping(message: Message):
    await message.answer("pong")

@router.message(F.text.in_({LABELS["contacts"]["ru"], LABELS["contacts"]["ka"]}))
async def on_contacts(message: Message):
    uid = message.from_user.id
    current = lang_of(uid)
    t = TXT[current]
    info = read_contacts()
    text = (
        f"{t['contacts_title']}\n"
        f"• {t['contacts_phone']}: {info['phone']}\n"
        f"• {t['contacts_email']}: {info['email']}\n"
        f"• {t['contacts_addr']}: {info['address']}"
    )
    await message.answer(text, reply_markup=make_main_kb(current))

@router.message(F.text.in_({LABELS["lang"]["ru"], LABELS["lang"]["ka"]}))
async def on_change_lang(message: Message):
    uid = message.from_user.id
    new_lang = toggle_lang(uid)
    # Повідомляємо про переключення (фрази навмисне «дзеркальні»)
    await message.answer(TXT[new_lang]["lang_switched"], reply_markup=make_main_kb(new_lang))

@router.message(F.text.in_({LABELS["back_channel"]["ru"], LABELS["back_channel"]["ka"]}))
async def on_back_to_channel(message: Message):
    uid = message.from_user.id
    current = lang_of(uid)
    if CHANNEL_URL:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=TXT[current]["open_channel"], url=CHANNEL_URL)]]
        )
        await message.answer(TXT[current]["open_channel"], reply_markup=kb)
    else:
        await message.answer(TXT[current]["no_channel"], reply_markup=make_main_kb(current))

# Будь-який інший текст — ігноруємо (нічого не відповідаємо)
# Просто не створюємо fallback-хендлер.
# Якщо дуже треба «абсолютна тиша», залишаємо так.
# Якщо хочеш логи — розкоментуй нижче:
# @router.message()
# async def _noop(_m: Message):
#     pass
