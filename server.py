# server.py
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram.types import Update

from bot import bot, dp  # імпортуємо готові bot & dispatcher

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# === ENV ===
BOT_TOKEN = os.environ["BOT_TOKEN"]                         # обов'язково у Render
WEBHOOK_BASE = os.environ["WEBHOOK_BASE"].rstrip("/")       # https://<твій-сервіс>.onrender.com
WEBHOOK_URL = f"{WEBHOOK_BASE}/webhook/{BOT_TOKEN}"

app = FastAPI()


# ---------- lifecycle ----------
@app.on_event("startup")
async def on_startup():
    # скидати старий вебхук і ставити новий на поточний домен
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    info = await bot.get_webhook_info()
    log.info("Webhook set -> %s url=%s", info.url == WEBHOOK_URL, info.url)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()


# ---------- health/debug ----------
@app.get("/")
async def root():
    info = await bot.get_webhook_info()
    return {"status": "ok", "webhook": info.url, "base": WEBHOOK_BASE}

@app.get("/debug/webhook")
async def debug_webhook_info():
    info = await bot.get_webhook_info()
    return info.model_dump()


# ---------- webhook ----------
# GET для перевірки в браузері (має повертати 200 OK)
@app.get("/webhook/{token}")
async def webhook_get(token: str):
    if token != BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook token (GET)")
    return {"ok": True, "method": "GET", "note": "Route exists; POST from Telegram is accepted."}

# Основний обробник від Telegram (POST)
@app.post("/webhook/{token}")
async def webhook_post(token: str, request: Request):
    if token != BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook token")
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}
