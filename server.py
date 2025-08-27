import os
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.client.default import DefaultBotProperties

from bot import dp, bot  # імпортуємо готові dispatcher та bot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_BASE = os.environ["WEBHOOK_BASE"].rstrip("/")
WEBHOOK_URL = f"{WEBHOOK_BASE}/webhook/{BOT_TOKEN}"

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    info = await bot.get_webhook_info()
    log.info("Webhook set -> %s url=%s", info.url == WEBHOOK_URL, info.url)

@app.get("/")
async def root():
    info = await bot.get_webhook_info()
    return {"status": "ok", "webhook": info.url, "base": WEBHOOK_BASE}

@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook token")
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}
