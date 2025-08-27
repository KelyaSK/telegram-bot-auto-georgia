# server.py
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram.types import Update
from bot import dp, bot  # імпортуємо готові dispatcher та bot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_BASE = os.environ["WEBHOOK_BASE"].rstrip("/")
WEBHOOK_URL = f"{WEBHOOK_BASE}/webhook/{BOT_TOKEN}"

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # скидаємо старий вебхук і ставимо правильний
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    info = await bot.get_webhook_info()
    log.info("Webhook set -> %s url=%s", info.url == WEBHOOK_URL, info.url)

@app.get("/")
async def root():
    info = await bot.get_webhook_info()
    return {"status": "ok", "webhook": info.url, "base": WEBHOOK_BASE}

# ✅ ДЕБАГ: GET-роут для перевірки в браузері (має відповідати 200 OK)
@app.get("/webhook/{token}")
async def debug_webhook_get(token: str):
    if token != BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook token (GET)")
    return {"ok": True, "method": "GET", "note": "This path exists and is ready for POST from Telegram."}

# ✅ Основний вебхук (POST) — сюди Telegram надсилатиме оновлення
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook token")
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

# Додатковий дебаг-роут (не обов’язково)
@app.get("/debug/webhook")
async def debug_webhook_info():
    info = await bot.get_webhook_info()
    return info.model_dump()
