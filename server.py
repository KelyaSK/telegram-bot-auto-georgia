import os
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram.types import Update
from dotenv import load_dotenv
from bot import bot, dp

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN    = os.getenv("BOT_TOKEN")
WEBHOOK_BASE = os.getenv("WEBHOOK_BASE")  # наприклад: https://your-app.onrender.com

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN не задан")
if not WEBHOOK_BASE:
    raise SystemExit("❌ WEBHOOK_BASE не задан")

BASE = WEBHOOK_BASE.rstrip("/")
if "/webhook" in BASE:
    raise SystemExit(f"❌ WEBHOOK_BASE має бути без /webhook: {WEBHOOK_BASE}")
if not BASE.startswith("https://"):
    raise SystemExit(f"❌ WEBHOOK_BASE повинен починатися з https://, зараз: {WEBHOOK_BASE}")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL  = f"{BASE}{WEBHOOK_PATH}"

app = FastAPI()

@app.on_event("startup")
async def on_startup():
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
        payload = await request.json()
        update = Update.model_validate(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bad update: {e}")
    await dp.feed_update(bot, update)
    return {"ok": True}
