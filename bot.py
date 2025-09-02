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
from aiogram.types.input_file import FSInputFile  # для відправки локальних файлів (aiogram v3)

# ---------- Files & ENV ----------
BASE_DIR = Path(__file__).parent
BANNER_PATH = BASE_DIR / "assets" / "banner.png"
DATA_JSON   = BASE_DIR / "data.json"
CHANNEL_URL = os.getenv("CHANNEL_URL")  # напр.: https://t.me/your_channel

# Зберігаємо вибір мови в оперативній пам'яті (скидається при рестарті процесу)
USER_LANG: Dict[int, str] = {}  # 'ru' | 'ka' | 'en'

# ---------- Тексти для RU / KA / EN ----------
TXT = {
    "ru": {
        "start_caption": (
            "Автотехника из США в Грузию — быстро и надёжно 🚢🇺🇸\n"
            "Машины, скутеры, квадроциклы и многое другое.\n\n"
            "Все предложения смотрите в нашем канале 📲\n"
            "Жмите кнопку ниже ⬇️"
        ),
        "menu_contacts": "📞 Контакты",
        "menu_lang": "🔁 Сменить язык",
        "menu_back_channel": "🔙 Назад в канал",

        "contacts_title": "📞 Контакты:",
        "contacts_phone": "Телефон",

        "lang_prompt": "🌐 Выберите язык интерфейса:",
        "lang_set": "Язык переключён на русский 🇷🇺",

        "open_channel_text": "Будем рады видеть вас в нашем канале! 📨",
        "open_channel_btn": "Перейти в канал ↗️",
        "no_channel": "Ссылка на канал пока не настроена.",

        "placeholder": "Выберите пункт...",
    },
    "ka": {
        "start_caption": (
            "ავტოტექნიკა აშშ-დან საქართველოში — სწრაფად და საიმედოდ 🚢🇺🇸\n"
            "ავტომობილები, სკუტერები, კვადროციკლები და ბევრი სხვა.\n\n"
            "ყველა შეთავაზება იხილეთ ჩვენს არხში 📲\n"
            "დააჭირეთ ღილაკს ქვემოთ ⬇️"
        ),
        "menu_contacts": "📞 კონტაქტები",
        "menu_lang": "🔁 ენის შეცვლა",
        "menu_back_channel": "🔙 არხზე დაბრუნება",

        "contacts_title": "📞 კონტაქტები:",
        "contacts_phone": "ტელეფონი",

        "lang_prompt": "🌐 აირჩიეთ ინტერფეისის ენა:",
        "lang_set": "ენა გადაერთო ქართულზე 🇬🇪",

        "open_channel_text": "სიხარულით დაგინახავთ ჩვენს არხში! 📨",
        "open_channel_btn": "არხში გადასვლა ↗️",
        "no_channel": "არხის ბმული ჯერ არ არის მითითებული.",

        "placeholder": "აირჩიეთ პუნქტი...",
    },
    "en": {
        "start_caption": (
            "We deliver vehicles & power sports from the USA to Georgia — fast and reliable 🚢🇺🇸\n"
            "Cars, jet skis, ATVs and more.\n\n"
            "See all offers in our channel 📲\n"
            "Choose an option below ⬇️"
        ),
        "menu_contacts": "📞 Contacts",
        "menu_lang": "🔁 Change language",
        "menu_back_channel": "🔙 Back to channel",

        "contacts_title": "📞 Contacts:",
        "contacts_phone": "Phone",

        "lang_prompt": "🌐 Choose interface language:",
        "lang_set": "Language switched to English 🇬🇧",

        "open_channel_text": "We’ll be glad to see you in our channel! 📨",
        "open_channel_btn": "Open channel ↗️",
        "no_channel": "Channel link is not configured yet.",

        "placeholder": "Choose an option...",
    },
}

LABELS = {
    "contacts":     {"ru": "📞 Контакты",      "ka": "📞 კონტაქტები",       "en": "📞 Contacts"},
    "lang":         {"ru": "🔁 Сменить язык",  "ka": "🔁 ენის შეცვლა",      "en": "🔁 Change language"},
    "back_channel": {"ru": "🔙 Назад в канал", "ka": "🔙 არხზე დაბრუნება",  "en": "🔙 Back to channel"},
}

def norm_lang(code: str) -> str:
    return code if code in ("ru", "ka", "en") else "ru"

def lang_of(uid: int) -> str:
    return USER_LANG.get(uid, "ru")

def set_lang(uid: int, code: str) -> str:
    code = norm_lang(code)
    USER_LANG[uid] = code
    return code

def read_contacts() -> Dict[str, Any]:
    """Зчитуємо дані з data.json. Достатньо поля 'phone' (рядок або кілька рядків)."""
    try:
        data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        return {
            "phone": data.get("phone", "—"),
        }
    except Exception:
        return {"phone": "—"}

def make_main_kb(lang: str) -> ReplyKeyboardMarkup:
    lang = norm_lang(lang)
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

def make_lang_choice_kb() -> InlineKeyboardMarkup:
    # Інлайн-вибір мови: RU / KA / EN
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Русский 🇷🇺",  callback_data="setlang:ru"),
            InlineKeyboardButton(text="ქართული 🇬🇪", callback_data="setlang:ka"),
            InlineKeyboardButton(text="English 🇬🇧", callback_data="setlang:en"),
        ]]
    )

router = Router()

# ---------- Handlers ----------

@router.message(CommandStart())
async def on_start(message: Message):
    uid = message.from_user.id
    lang = lang_of(uid)
    kb = make_main_kb(lang)

    # Банер + клавіатура в одному повідомленні
    if BANNER_PATH.exists():
        photo = FSInputFile(str(BANNER_PATH))
        await message.answer_photo(photo=photo, caption=TXT[lang]["start_caption"], reply_markup=kb)
    else:
        await message.answer(TXT[lang]["start_caption"], reply_markup=kb)

@router.message(Command("ping"))
async def on_ping(message: Message):
    await message.answer("pong")

@router.message(F.text.in_({LABELS["contacts"]["ru"], LABELS["contacts"]["ka"], LABELS["contacts"]["en"]}))
async def on_contacts(message: Message):
    """Показуємо лише телефони з data.json (без email та адреси)."""
    uid = message.from_user.id
    lang = lang_of(uid)
    t = TXT[lang]
    c = read_contacts()

    text = f"{t['contacts_title']}\n• {t['contacts_phone']}: {c['phone']}"
    await message.answer(text, reply_markup=make_main_kb(lang))

@router.message(F.text.in_({LABELS["lang"]["ru"], LABELS["lang"]["ka"], LABELS["lang"]["en"]}))
async def on_change_lang(message: Message):
    uid = message.from_user.id
    lang = lang_of(uid)
    await message.answer(TXT[lang]["lang_prompt"], reply_markup=make_lang_choice_kb())

@router.callback_query(F.data.startswith("setlang:"))
async def on_set_lang(call: CallbackQuery):
    uid = call.from_user.id
    _, code = call.data.split(":", 1)
    new_lang = set_lang(uid, code)

    await call.message.answer(TXT[new_lang]["lang_set"], reply_markup=make_main_kb(new_lang))
    await call.answer()

@router.message(F.text.in_({LABELS["back_channel"]["ru"], LABELS["back_channel"]["ka"], LABELS["back_channel"]["en"]}))
async def on_back_channel(message: Message):
    lang = lang_of(message.from_user.id)
    if CHANNEL_URL:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=TXT[lang]["open_channel_btn"], url=CHANNEL_URL)]]
        )
        await message.answer(TXT[lang]["open_channel_text"], reply_markup=kb)
    else:
        await message.answer(TXT[lang]["no_channel"], reply_markup=make_main_kb(lang))

# Інші повідомлення — повна тиша
@router.message()
async def _noop(_msg: Message):
    pass
