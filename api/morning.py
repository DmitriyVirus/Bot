# api/morning.py
import os
import random
import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from tgbot import tgbot

router = APIRouter()

URLS_DIR = os.path.join(os.getcwd(), "urls")

GOOD_MORNING_MAPPING = {
    0: ("Понедельник… держимся 💀", "mond_url.txt"),
    4: ("ПЯТНИЦА!!! 🎉", "fri_url.txt"),
    5: ("Выходныеее 😎", "weekend_url.txt"),
    6: ("Выходныеее 😎", "weekend_url.txt"),
}
GOOD_MORNING_DEFAULT = ("Доброе утро ☀️", "workdays_url.txt")

CHAT_ID = int(os.environ.get("CHAT_ID"))

async def send_photo(chat_id: int, photo_url: str, caption: str):
    await tgbot.bot.send_photo(chat_id=chat_id, photo=photo_url, caption=caption)

@router.get("/api/cron/good_morning")
async def cron_good_morning():
    try:
        day = datetime.datetime.now().weekday()
        text, file_name = GOOD_MORNING_MAPPING.get(day, GOOD_MORNING_DEFAULT)

        path = os.path.join(URLS_DIR, file_name)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Файл {file_name} не найден")

        with open(path, "r", encoding="utf-8") as f:
            urls = [u.strip() for u in f if u.strip()]

        if not urls:
            raise HTTPException(status_code=404, detail="Список URL пуст")

        photo_url = random.choice(urls)

        await send_photo(CHAT_ID, photo_url, text)

        return JSONResponse({
            "status": "ok",
            "chat_id": CHAT_ID,
            "text": text,
            "photo_url": photo_url
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
