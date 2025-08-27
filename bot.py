# -*- coding: utf-8 -*-
import os
import re
import json
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types.input_file import FSInputFile, BufferedInputFile

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

# ------------- ENV -------------
load_dotenv()
BOT_TOKEN       = os.getenv("BOT_TOKEN")
CHANNEL_URL     = os.getenv("CHANNEL_URL", "https://t.me/your_channel")
ADMIN_CHAT_ID   = os.getenv("ADMIN_CHAT_ID")  # str ok
START_IMAGE_PATH = Path(os.getenv("START_IMAGE_PATH", "assets/Frame81.png"))
START_IMAGE_URL  = os.getenv("START_IMAGE_URL", "https://i.imgur.com/3ZQ3ZyK.png")

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN не задан")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher()

# ------------- локалізація -------------
# простий словничок
TXT = {
    "ru": {
        "welcome": "👋 Добро пожаловать!\nНажмите «/start» и получите контакты и помощь по авто 🚘",
        "menu_hint": "Выберите действие ниже 👇",
        "to_channel": "↩️ Вернитесь в канал по кнопке ниже:",
        "contacts_title": "Контактная информация",
        "leave_prompt": "✍️ Оставьте контакт для связи.\nЛучше всего — нажмите кнопку ниже, чтобы поделиться номером.\nИли пришлите номер текстом.",
        "share_phone": "📲 Поделиться телефоном",
        "back": "⬅️ Назад",
        "change_lang": "🌐 Сменить язык",
        "left_ok": "👍 Спасибо! Мы свяжемся с вами.",
        "notify_admin_tpl": "🆕 Лид из бота\n<b>Пользователь:</b> {name} (id {uid})\n<b>Юзернейм:</b> @{uname}\n<b>Контакт:</b> {contact}",
        "contacts_btn": "📞 Контакты",
        "back_btn": "🔙 Назад в канал",
        "leave_btn": "📝 Оставить контакты",
        "img_error": "⚠️ Ошибка при загрузке изображения",
        "lang_pick": "Выберите язык:",
        "number_invalid": "❗ Введите корректный номер или нажмите кнопку поделиться."
    },
    "ka": {
        "welcome": "👋 კეთილი იყოს მობრძანება!\nდააჭირეთ «/start» და მიიღეთ კონტაქტები და დახმარება 🚘",
        "menu_hint": "აირჩიეთ ქმედება ქვემოთ 👇",
        "to_channel": "↩️ არხზე დასაბრუნებლად დააჭირეთ ქვემოთ:",
        "contacts_title": "საკონტაქტო ინფორმაცია",
        "leave_prompt": "✍️ დატოვეთ საკონტაქტო ნომერი.\nსჯობს დააჭიროთ ქვემოთ ღილაკს, რომ გააზიაროთ ნომერი.",
        "share_phone": "📲 გაუზიარე ტელეფონი",
        "back": "⬅️ უკან",
        "change_lang": "🌐 ენის შეცვლა",
        "left_ok": "👍 მადლობა! მალე დაგიკავშირდებით.",
        "notify_admin_tpl": "🆕 ლიდი ბოტიდან\n<b>მომხმარებელი:</b> {name} (id {uid})\n<b>იუზერნეიმი:</b> @{uname}\n<b>კონტაქტი:</b> {contact}",
        "contacts_btn": "📞 კონტაქტები",
        "back_btn": "🔙 არხზე დაბრუნება",
        "leave_btn": "📝 დატოვე კონტაქტი",
        "img_error": "⚠️ სურათის ჩატვირთვის შეცდომა",
        "lang_pick": "აირჩიეთ ენა:",
        "number_invalid": "❗ შეიყვანეთ სწორი ნომერი ან გაუზიარეთ ტელეფონი."
    }
}

# збереження вибору мови (in-memory)
USER_LANG: dict[int, str] = {}

def get_lang(user_id: int) -> str:
    return USER_LANG.get(user_id, "ru")

# ------------- клавіатури -------------
def main_menu(lang="ru") -> ReplyKeyboardMarkup:
    texts = TXT[lang]
    kb = ReplyKeyboardBuilder()
    kb.button(text=texts["contacts_btn"])
    kb.button(text=texts["back_btn"])
    kb.button(text=texts["leave_btn"])
    kb.button(text=texts["change_lang"])
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)

def back_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться в канал", url=CHANNEL_URL)]
    ])

def lang_picker_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский",  callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇪 ქართული", callback_data="lang:ka"),
    ]])

def share_phone_kb(lang="ru") -> ReplyKeyboardMarkup:
    texts = TXT[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts["share_phone"], request_contact=True)],
            [KeyboardButton(text=texts["back"])]
        ],
        resize_keyboard=True
    )

# ------------- data.json -------------
def load_contacts_raw() -> dict:
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print(f"⚠️ data.json не найден. cwd={os.getcwd()}")
        return {}
    except Exception as e:
        print(f"⚠️ Ошибка чтения data.json: {e}")
        return {}

def render_contacts_text(data: dict, lang="ru") -> str:
    if isinstance(data.get("items"), list):
        title = str(data.get("title") or TXT[lang]["contacts_title"])
        lines = [f"<b>{title}</b>", ""]
        for it in data["items"]:
            name = str(it.get("name", "")).strip()
            value = str(it.get("value", "")).strip()
            url = str(it.get("url", "")).strip() if it.get("url") else ""
            if not (name or value or url):
                continue
            if url:
                lines.append(f"• <b>{name}:</b> <a href='{url}'>{value or url}</a>")
            else:
                lines.append(f"• <b>{name}:</b> {value or '—'}")
        return "\n".join(lines) if len(lines) > 2 else "—"
    phone   = data.get("phone", "—")
    email   = data.get("email", "—")
    address = data.get("address", "—")
    return (f"☎️ <b>Телефон:</b> {phone}\n"
            f"✉️ <b>Email:</b> {email}\n"
            f"📍 <b>Адрес:</b> {address}")

# ------------- зображення -------------
async def send_start_image(message: Message, caption: str, lang="ru"):
    print(f"🖼 cwd={os.getcwd()}")
    assets_dir = Path("assets")
    print(f"🖼 assets exists={assets_dir.exists()} contents={list(assets_dir.iterdir()) if assets_dir.exists() else 'N/A'}")
    print(f"🖼 START_IMAGE_PATH={START_IMAGE_PATH.resolve()} exists={START_IMAGE_PATH.exists()}")

    if START_IMAGE_PATH.exists() and START_IMAGE_PATH.is_file():
        try:
            await message.answer_photo(
                photo=FSInputFile(START_IMAGE_PATH),
                caption=caption,
                reply_markup=main_menu(lang)
            )
            return
        except Exception as e:
            print(f"⚠️ Ошибка отправки локального файла: {e}")

    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(START_IMAGE_URL, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    await message.answer_photo(
                        photo=BufferedInputFile(data, filename="start.jpg"),
                        caption=caption,
                        reply_markup=main_menu(lang)
                    )
                    return
                print(f"⚠️ START_IMAGE_URL HTTP {resp.status}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки по URL: {e}")

    await message.answer(TXT[lang]["img_error"], reply_markup=main_menu(lang))

# ------------- Хендлери -------------
@dp.message(Command("start"))
async def start_cmd(message: Message):
    lang = get_lang(message.from_user.id)
    await send_start_image(message, TXT[lang]["welcome"], lang)

@dp.message(F.text.in_(["📞 Контакты", "📞 კონტაქტები"]))
async def show_contacts(message: Message):
    lang = get_lang(message.from_user.id)
    text = render_contacts_text(load_contacts_raw(), lang)
    await message.answer(text, reply_markup=main_menu(lang))

@dp.message(F.text.in_(["🔙 Назад в канал", "🔙 არხზე დაბრუნება"]))
async def back_to_channel(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(TXT[lang]["to_channel"], reply_markup=back_inline_kb())

# ——— кнопка смены языка
@dp.message(F.text.in_(["🌐 Сменить язык", "🌐 ენის შეცვლა"]))
async def change_lang(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(TXT[lang]["lang_pick"], reply_markup=lang_picker_kb())

@dp.callback_query(F.data.startswith("lang:"))
async def lang_selected(cb):
    lang = cb.data.split(":")[1]
    USER_LANG[cb.from_user.id] = lang
    await cb.message.answer(TXT[lang]["menu_hint"], reply_markup=main_menu(lang))
    await cb.answer("OK")

# ——— кнопка оставить контакты (підтримує також UA фразу, якщо ти її натискав)
@dp.message(F.text.in_(["📝 Оставить контакты", "📝 დატოვე კონტაქტი", "📝 Залишити контакти"]))
async def leave_contacts(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(TXT[lang]["leave_prompt"], reply_markup=share_phone_kb(lang))

# ——— приймаємо контакт від кнопки «Поделиться телефоном»
@dp.message(F.contact)
async def got_contact(message: Message):
    lang = get_lang(message.from_user.id)
    contact = message.contact
    user = message.from_user

    info = TXT[lang]["notify_admin_tpl"].format(
        name=f"{user.full_name}",
        uid=user.id,
        uname=(user.username or "—"),
        contact=contact.phone_number
    )
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(int(ADMIN_CHAT_ID), info)
        except Exception as e:
            print(f"⚠️ Не удалось отправить лид админу: {e}")

    await message.answer(TXT[lang]["left_ok"], reply_markup=main_menu(lang))

# ——— якщо користувач надсилає номер текстом
PHONE_RE = re.compile(r"[+]?[\d\s\-()]{7,}")

@dp.message(F.text.regexp(PHONE_RE))
async def got_phone_text(message: Message):
    lang = get_lang(message.from_user.id)
    phone = message.text.strip()
    user  = message.from_user

    info = TXT[lang]["notify_admin_tpl"].format(
        name=f"{user.full_name}",
        uid=user.id,
        uname=(user.username or "—"),
        contact=phone
    )
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(int(ADMIN_CHAT_ID), info)
        except Exception as e:
            print(f"⚠️ Не удалось отправить лид админу: {e}")

    await message.answer(TXT[lang]["left_ok"], reply_markup=main_menu(lang))

# ——— кнопка «Назад» в режимі залишення контакту
@dp.message(F.text.in_(["⬅️ Назад", "⬅️ უკან"]))
async def back_from_lead(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(TXT[lang]["menu_hint"], reply_markup=main_menu(lang))

# ------------- Healthcheck для Render -------------
async def healthcheck(request):
    return web.Response(text="✅ Bot is running")

async def start_web_app():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌍 Web server running on port {port}")

# ------------- RUN -------------
async def main():
    asyncio.create_task(start_web_app())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🤖 Bot starting...")
    asyncio.run(main())
