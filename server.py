# server.py
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram.types import Update
from dotenv import load_dotenv

# імпортуємо bot та dp з твоєї логіки
from bot import bot, dp

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_BASE = os.getenv("WEBHOOK_BASE")  # приклад: https://telegram-bot-auto-georgia-ba2a.onrender.com
if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN не задан у змінних середовища")
if not WEBHOOK_BASE:
    raise SystemExit("❌ WEBHOOK_BASE не задан у змінних середовища")

# Нормалізуємо URL та будуємо повний шлях вебхука
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_BASE.rstrip('/')}{WEBHOOK_PATH}"

# Перевірка формату — Telegram вимагає ПОВНИЙ https URL
if not WEBHOOK_URL.startswith("https://"):
    raise SystemExit(f"❌ WEBHOOK_URL має бути https: {WEBHOOK_URL}")

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    # Ставимо вебхук при старті
    ok = await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logging.info(f"Webhook set -> {ok} url={WEBHOOK_URL}")


@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()


@app.get("/")
async def health():
    return {"status": "ok", "webhook": WEBHOOK_URL}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        update = Update.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Bad update: {e}")

    # передаємо апдейт у диспетчер
    await dp.feed_update(bot, update)
    return {"ok": True}
