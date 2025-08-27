# server.py
import os
import asyncio
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from bot import router

# ----- ENV -----
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_BASE = os.getenv("WEBHOOK_BASE")  # ПОВИННО БУТИ без /webhook і без токена! Напр.: https://telegram-bot-auto-georgia-1.onrender.com

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
if not WEBHOOK_BASE:
    raise RuntimeError("WEBHOOK_BASE is not set")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_BASE.rstrip('/')}{WEBHOOK_PATH}"

# ----- LOGGING -----
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

# ----- APP/BOT/DP -----
app = FastAPI()
bot = Bot(BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def _set_webhook_safely() -> bool:
    """
    Прагматично ставимо вебхук. Не падаємо, якщо Telegram повернув помилку.
    Повертаємо True/False, щоб показати статус у / та /force_set_webhook.
    """
    try:
        # Скидаємо старий вебхук і ставимо новий
        log.info("Deleting old webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(0.1)

        allowed = ["message", "callback_query"]
        log.info("Setting webhook to %s (allowed_updates=%s)", WEBHOOK_URL, allowed)
        ok = await bot.set_webhook(url=WEBHOOK_URL, allowed_updates=allowed, max_connections=40)
        if not ok:
            log.error("set_webhook returned False")
        return bool(ok)
    except Exception as e:
        log.exception("set_webhook failed: %s", e)
        return False

# ----- LIFECYCLE -----
@app.on_event("startup")
async def on_startup() -> None:
    # Не валимо сервіс, навіть якщо set_webhook не пройшов.
    # Сервіс підніметься, і ти зможеш поставити вебхук руками або через /force_set_webhook.
    await _set_webhook_safely()
    await asyncio.sleep(0.2)

@app.on_event("shutdown")
async def on_shutdown() -> None:
    await bot.session.close()

# ----- ROUTES -----
@app.get("/")
async def root() -> Dict[str, Any]:
    info = await bot.get_webhook_info()
    return {
        "status": "ok",
        "webhook": {
            "expected": WEBHOOK_URL,  # для наочності
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "ip_address": info.ip_address,
            "max_connections": info.max_connections,
            "allowed_updates": info.allowed_updates,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
        },
    }

@app.get("/force_set_webhook")
async def force_set_webhook() -> Dict[str, Any]:
    """
    Ручний виклик: /force_set_webhook
    Спробувати поставити вебхук ще раз і повернути статус.
    """
    ok = await _set_webhook_safely()
    info = await bot.get_webhook_info()
    return {
        "forced": ok,
        "webhook": {
            "expected": WEBHOOK_URL,
            "url": info.url,
            "last_error_message": info.last_error_message,
        },
    }

# GET для швидкого чеку у браузері
@app.get(WEBHOOK_PATH)
async def webhook_get() -> Dict[str, bool]:
    return {"ok": True}

# POST для Telegram
@app.post(WEBHOOK_PATH)
async def webhook_post(request: Request) -> JSONResponse:
    token_in_path = request.url.path.split("/")[-1]
    if token_in_path != BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    data = await request.json()
    log.info("Update received: %s", data)
    try:
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return JSONResponse({"ok": True})
    except Exception as e:
        log.exception("Error while processing update: %s", e)
        return JSONResponse({"ok": False, "error": str(e)})
