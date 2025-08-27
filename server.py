# -*- coding: utf-8 -*-
import os
import re
import json
import asyncio
from pathlib import Path
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, Update
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types.input_file import FSInputFile, BufferedInputFile

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

# ---------------- ENV ----------------
load_dotenv()
BOT_TOKEN      = os.getenv("BOT_TOKEN")
CHANNEL_URL    = os.getenv("CHANNEL_URL", "https://t.me/your_channel")
ADMIN_CHAT_ID  = os.getenv("ADMIN_CHAT_ID")  # str ок
START_IMAGE_PATH = Path(os.getenv("START_IMAGE_PATH", "assets/Frame81.png"))
START_IMAGE_URL  = os.getenv("START_IMAGE_URL", "https://i.imgur.com/3ZQ3ZyK.png")

# обов’язково вкажи в Render: https://<твій-сервіс>.onrender.com
WEBHOOK_BASE   = os.getenv("WEBHOOK_BASE")  # напр. https://telegram-bot-auto-georgia-xxx.onrender.com
WEBHOOK_PATH   = os.getenv("WEBHOOK_PATH", "webhook")  # не міняти, якщо не треба
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change_me_long_random_string")  # довгий секрет

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN не задан")

# ---------------- BOT CORE ----------------
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher()

# локалізація
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
USER_LANG: dict[int, str] = {}
def get_lang(uid: int) -> str: return USER_LANG.get(uid, "ru")

# клавіатури
def main_menu(lang="ru") -> ReplyKeyboardMarkup:
    t = TXT[lang]
    kb = ReplyKeyboardBuilder()
    kb.button(text=t["contacts_btn"])
    kb.button(text=t["back_btn"])
    kb.button(text=t["leave_btn"])
    kb.button(text=t["change_lang"])
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
    t = TXT[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["share_phone"], request_contact=True)],
            [KeyboardButton(text=t["back"])]
        ],
        resize_keyboard=True
    )

# data.json
def load_contacts_raw() -> Dict[str, Any]:
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

# банер
async def send_start_image(message: Message, caption: str, lang="ru"):
    print(f"🖼 cwd={os.getcwd()}")
    assets_dir = Path("assets")
    print(f"🖼 assets exists={assets_dir.exists()} contents={list(assets_dir.iterdir()) if assets_dir.exists() else 'N/A'}")
    print(f"🖼 START_IMAGE_PATH={START_IMAGE_PATH.resolve()} exists={START_IMAGE_PATH.exists()}")

    if START_IMAGE_PATH.exists() and START_IMAGE_PATH.is_file():
        try:
            await message.answer_photo(photo=FSInputFile(START_IMAGE_PATH), caption=caption, reply_markup=main_menu(lang))
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

# --------- handlers (aiogram) ----------
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

@dp.message(F.text.in_(["📝 Оставить контакты", "📝 დატოვე კონტაქტი", "📝 Залишити контакти"]))
async def leave_contacts(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(TXT[lang]["leave_prompt"], reply_markup=share_phone_kb(lang))

@dp.message(F.contact)
async def got_contact(message: Message):
    lang = get_lang(message.from_user.id)
    c = message.contact
    u = message.from_user
    info = TXT[lang]["notify_admin_tpl"].format(
        name=u.full_name, uid=u.id, uname=(u.username or "—"), contact=c.phone_number
    )
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(int(ADMIN_CHAT_ID), info)
        except Exception as e:
            print(f"⚠️ Не удалось отправить лид админу: {e}")
    await message.answer(TXT[lang]["left_ok"], reply_markup=main_menu(lang))

PHONE_RE = re.compile(r"[+]?[\d\s\-()]{7,}")
@dp.message(F.text.regexp(PHONE_RE))
async def got_phone_text(message: Message):
    lang = get_lang(message.from_user.id)
    phone = message.text.strip()
    u = message.from_user
    info = TXT[lang]["notify_admin_tpl"].format(
        name=u.full_name, uid=u.id, uname=(u.username or "—"), contact=phone
    )
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(int(ADMIN_CHAT_ID), info)
        except Exception as e:
            print(f"⚠️ Не удалось отправить лид админу: {e}")
    await message.answer(TXT[lang]["left_ok"], reply_markup=main_menu(lang))

# --------- AIOHTTP (webhook server) ----------
routes = web.RouteTableDef()

@routes.get("/")
async def health(_: web.Request):
    return web.Response(text="✅ Bot webhook is live")

@routes.get("/set-webhook")
async def set_webhook(_: web.Request):
    if not WEBHOOK_BASE:
        return web.Response(text="❌ Set WEBHOOK_BASE env first", status=400)
    url = f"{WEBHOOK_BASE.rstrip('/')}/{WEBHOOK_PATH}/{BOT_TOKEN}"
    ok = await bot.set_webhook(url, secret_token=WEBHOOK_SECRET, drop_pending_updates=True)
    return web.Response(text=f"set_webhook -> {ok} to {url}")

@routes.post(f"/{WEBHOOK_PATH}" + "/{token}")
async def webhook(request: web.Request):
    # 1) перевіряємо токен у шляху (примітивний захист від чужих постів)
    token_in_path = request.match_info.get("token", "")
    if token_in_path != BOT_TOKEN:
        return web.Response(status=403, text="forbidden")

    # 2) перевіряємо секретний заголовок Telegram (ще один шар захисту)
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != WEBHOOK_SECRET:
        return web.Response(status=403, text="bad secret")

    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="ok")

async def on_startup(app: web.Application):
    # реєструємо webhook автоматично, якщо WEBHOOK_BASE заданий
    if WEBHOOK_BASE:
        url = f"{WEBHOOK_BASE.rstrip('/')}/{WEBHOOK_PATH}/{BOT_TOKEN}"
        ok = await bot.set_webhook(url, secret_token=WEBHOOK_SECRET, drop_pending_updates=True)
        print(f"🔔 set_webhook({url}) -> {ok}")
    else:
        print("⚠️ WEBHOOK_BASE не задан — відкрити /set-webhook вручну після деплою")

async def on_cleanup(app: web.Application):
    await bot.session.close()

def build_app() -> web.Application:
    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app

if __name__ == "__main__":
    # Render підставляє PORT
    port = int(os.environ.get("PORT", "10000"))
    web.run_app(build_app(), host="0.0.0.0", port=port)
