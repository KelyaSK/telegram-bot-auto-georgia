# -*- coding: utf-8 -*-
import os
import json
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types.input_file import FSInputFile, BufferedInputFile

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

# ---------------------- ENV ----------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/your_channel")

# Можеш вказати свій шлях/URL у Render → Environment (рекомендовано)
START_IMAGE_PATH = Path(os.getenv("START_IMAGE_PATH", "assets/Frame81.png"))
START_IMAGE_URL  = os.getenv("START_IMAGE_URL", "https://i.imgur.com/3ZQ3ZyK.png")

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN не задан")

# ---------------------- BOT ----------------------
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ---------------------- UI ----------------------
def main_menu(lang="ru"):
    kb = ReplyKeyboardBuilder()
    if lang == "ka":
        kb.button(text="📞 კონტაქტები")
        kb.button(text="🔙 არხზე დაბრუნება")
    else:
        kb.button(text="📞 Контакты")
        kb.button(text="🔙 Назад в канал")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def back_inline_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Вернуться в канал", url=CHANNEL_URL)]]
    )

# ---------------------- DATA ----------------------
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

def render_contacts_text(data: dict) -> str:
    # формат 2: {"title": "...", "items":[{"name": "...", "value": "...", "url": "..."}]}
    if isinstance(data.get("items"), list):
        title = str(data.get("title") or "Контактная информация")
        lines = [f"<b>{title}</b>", ""]
        for it in data["items"]:
            name = str(it.get("name", "")).strip()
            value = str(it.get("value", "")).strip()
            url = str(it.get("url", "")).strip() if it.get("url") else ""
            if not name and not value and not url:
                continue
            line = f"• <b>{name}:</b> "
            line += f"<a href='{url}'>{value or url}</a>" if url else (value or "—")
            lines.append(line)
        return "\n".join(lines) if len(lines) > 2 else "Контакты пока не заполнены."

    # формат 1: простые поля
    phone   = data.get("phone", "—")
    email   = data.get("email", "—")
    address = data.get("address", "—")
    return (f"☎️ <b>Телефон:</b> {phone}\n"
            f"✉️ <b>Email:</b> {email}\n"
            f"📍 <b>Адрес:</b> {address}")

# ---------------------- IMAGE HELPERS ----------------------
async def send_start_image(message: Message, caption: str):
    # Диагностика для Render
    print(f"🖼 cwd={os.getcwd()}")
    assets_dir = Path("assets")
    print(f"🖼 assets exists={assets_dir.exists()} contents={list(assets_dir.iterdir()) if assets_dir.exists() else 'N/A'}")
    print(f"🖼 START_IMAGE_PATH={START_IMAGE_PATH.resolve()} exists={START_IMAGE_PATH.exists()}")

    # 1) локальный файл
    if START_IMAGE_PATH.exists() and START_IMAGE_PATH.is_file():
        try:
            photo = FSInputFile(START_IMAGE_PATH)
            await message.answer_photo(photo=photo, caption=caption, reply_markup=main_menu("ru"))
            return
        except Exception as e:
            print(f"⚠️ Ошибка отправки локального файла: {e}")

    # 2) скачать по URL и отправить как буфер (чтобы не зависеть от ограничений Telegram на внешние URL)
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(START_IMAGE_URL, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    buf = BufferedInputFile(data, filename="start.jpg")
                    await message.answer_photo(photo=buf, caption=caption, reply_markup=main_menu("ru"))
                    return
                else:
                    print(f"⚠️ Не удалось скачать START_IMAGE_URL. HTTP {resp.status}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки по URL: {e}")

    # 3) окончательное сообщение, если ничего не вышло
    await message.answer("⚠️ Ошибка при загрузке изображения", reply_markup=main_menu("ru"))

# ---------------------- HANDLERS ----------------------
@dp.message(Command("start"))
async def start_cmd(message: Message):
    caption = "👋 Добро пожаловать!\nНажмите «/start» и получите контакты и помощь по авто 🚘"
    await send_start_image(message, caption)

@dp.message(F.text.in_(["📞 Контакты", "📞 კონტაქტები"]))
async def show_contacts(message: Message):
    text = render_contacts_text(load_contacts_raw())
    await message.answer(text, reply_markup=main_menu("ru"))

@dp.message(F.text.in_(["🔙 Назад в канал", "🔙 არხზე დაბრუნება"]))
async def back_to_channel(message: Message):
    await message.answer("↩️ Вернитесь в канал по кнопке ниже:", reply_markup=back_inline_kb())

# ---------------------- Healthcheck (Render free Web Service) ----------------------
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

# ---------------------- RUN ----------------------
async def main():
    # маленький веб-сервер для Render
    asyncio.create_task(start_web_app())

    # бот
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🤖 Bot starting...")
    asyncio.run(main())
