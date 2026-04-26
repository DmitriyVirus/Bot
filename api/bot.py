import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tgbot import tgbot
from api.cron import router as cron_router
from api.sheets_api import router as sheets_router
from api.backupbot import router as backup_router
from api.morning import router as morning_router

logger = logging.getLogger(__name__)

# ==============================
# Lifespan (вместо устаревших on_event)
# ==============================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Setting webhook...")
        await tgbot.set_webhook()
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
    yield
    # Shutdown
    await tgbot.bot.session.close()
    logger.info("Bot session closed.")


app = FastAPI(lifespan=lifespan)

app.include_router(cron_router)
app.include_router(sheets_router)
app.include_router(backup_router)
app.include_router(morning_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ==============================
# Страница
# ==============================
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def read_root():
    return FileResponse(os.path.join(os.getcwd(), "index.html"))


# ==============================
# Webhook — с проверкой secret_token
# ==============================
TELEGRAM_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

@app.post("/api/bot")
async def tgbot_webhook_route(request: Request):
    # Проверка secret_token от Telegram (если задан в env)
    if TELEGRAM_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != TELEGRAM_SECRET:
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        update_dict = await request.json()
        logger.debug(f"Received update: {json.dumps(update_dict, indent=2)}")
        await tgbot.update_bot(update_dict)
        return ""
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {"error": str(e)}
