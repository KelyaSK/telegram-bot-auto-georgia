# bot.py
import json
import os
from pathlib import Path
from typing import Dict, Any

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile,
)

# ---------- Files & ENV ----------
BASE_DIR = Path(__file__).parent
BANNER_PATH = BASE_DIR / "assets" / "banner.png"
DATA_JSON = BASE_DIR / "data.json"
CHANNEL_URL = os.getenv("CHANNEL_URL")

USER_LANG: Dict[int, str] = {}

# ---------- Texts ----------
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
        "placeholder": "Выберите пункт...",
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
        "lang_switched": "ენა შეიცვალა русულზე.",
        "open_channel": "არხის გახსნა",
        "no_channel": "არხის ბმული არ არის მითითებული.",
        "placeholder": "აირჩიეთ პუნქტი...",
    },
}

LABELS = {
    "contacts": {"ru": "📞 Контакты", "ka": "📞 კონტაქტები"},
    "lang": {"ru": "🔁 Сменить язык", "ka": "🔁 ენის შეცვლა"},
    "back_channel": {"ru": "🔙 Назад в канал", "ka": "🔙 არხზე დაბრუნება"},
}

def lang_of(uid: int) -> str:
    return USER_LANG.get(uid, "ru")

def toggle_lang(uid: int) -> str:
    new_lang = "ka" if lang_of(uid) == "ru" else "ru"
    USER_LANG[uid] = new_lang
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
    t = TXT[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LABELS["contacts"][lang])],
            [KeyboardButton(text=LABELS["lang"][lang])],
            [KeyboardButton(text=LABELS["back_channel"][lang])],
        ],
        resize_keyboard=True,
        input_field_placeholder=t["placeholder"],
    )

router = Router()

# ---------- Handlers ----------

@router.message(CommandStart())
async def on_start(message: Message):
    uid = message.from_user.id
    lang = lang_of(uid)
    kb = make_main_kb(lang)

    if BANNER_PATH.exists():
        photo = FSInputFile(str(BANNER_PATH))
        await message.answer_photo(
            photo=photo,
            caption=TXT[lang]["start_caption"],
            reply_markup=kb   # <-- клавіатура тут
        )
    else:
        await message.answer(TXT[lang]["start_caption"], reply_markup=kb)

@router.message(Command("ping"))
async def on_ping(message: Message):
    await message.answer("pong")

@router.message(F.text.in_({LABELS["contacts"]["ru"], LABELS["contacts"]["ka"]}))
async def on_contacts(message: Message):
    uid = message.from_user.id
    lang = lang_of(uid)
    t = TXT[lang]
    c = read_contacts()
    text = (
        f"{t['contacts_title']}\n"
        f"• {t['contacts_phone']}: {c['phone']}\n"
        f"• {t['contacts_email']}: {c['email']}\n"
        f"• {t['contacts_addr']}: {c['address']}"
    )
    await message.answer(text, reply_markup=make_main_kb(lang))

@router.message(F.text.in_({LABELS["lang"]["ru"], LABELS["lang"]["ka"]}))
async def on_change_lang(message: Message):
    uid = message.from_user.id
    new_lang = toggle_lang(uid)
    await message.answer(TXT[new_lang]["lang_switched"], reply_markup=make_main_kb(new_lang))

@router.message(F.text.in_({LABELS["back_channel"]["ru"], LABELS["back_channel"]["ka"]}))
async def on_back_channel(message: Message):
    lang = lang_of(message.from_user.id)
    if CHANNEL_URL:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=TXT[lang]["open_channel"], url=CHANNEL_URL)]]
        )
        await message.answer(TXT[lang]["open_channel"], reply_markup=kb)
    else:
        await message.answer(TXT[lang]["no_channel"], reply_markup=make_main_kb(lang))

# Інші повідомлення — повна тиша
@router.message()
async def _noop(_msg: Message):
    pass
