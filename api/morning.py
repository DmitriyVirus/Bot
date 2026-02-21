import os
import random
import datetime
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from tgbot import tgbot
from tgbot.sheets.gspread_client import get_gspread_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Конфиги
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))
SHEET_NAME = os.environ.get("SHEET_NAME", "DareDevils")
WORKSHEET_NAME = "Утро"

# Соответствие дня недели столбцам Google Sheet
DAY_MAPPING = {
    0: "monday",
    1: "workdays",
    2: "workdays",
    3: "workdays",
    4: "friday",
    5: "weekends",
    6: "weekends"
}

# Текст подписей по дню
TEXT_MAPPING = {
    0: "Понедельник… держимся 💀",
    1: "Доброе утро ☀️",
    2: "Доброе утро ☀️",
    3: "Доброе утро ☀️",
    4: "ПЯТНИЦА!!! 🎉",
    5: "Выходныеее 😎",
    6: "Выходныеее 😎",
}

# ===== вспомогательные функции =====
def get_worksheet():
    try:
        client = get_gspread_client()
        return client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
    except Exception as e:
        logger.error(f"Не удалось открыть лист {WORKSHEET_NAME}: {e}")
        return None

def get_urls_for_day(day_index: int):
    sheet = get_worksheet()
    if not sheet:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к Google Sheets")
    
    column_name = DAY_MAPPING.get(day_index)
    if not column_name:
        column_name = "workdays"

    all_records = sheet.get_all_records()
    urls = []
    for row in all_records:
        url = row.get(column_name)
        if url and url.strip():
            urls.append(url.strip())
    return urls

async def send_photo(chat_id: int, photo_url: str, caption: str):
    await tgbot.bot.send_photo(chat_id=chat_id, photo=photo_url, caption=caption)

# ===== endpoint =====
@router.get("/api/cron/good_morning")
async def cron_good_morning():
    try:
        day = datetime.datetime.now().weekday()
        text = TEXT_MAPPING.get(day, "Доброе утро ☀️")
        urls = get_urls_for_day(day)

        if not urls:
            raise HTTPException(status_code=404, detail="Ссылки для этого дня не найдены")

        photo_url = random.choice(urls)
        await send_photo(CHAT_ID, photo_url, text)

        return JSONResponse({
            "status": "ok",
            "chat_id": CHAT_ID,
            "text": text,
            "photo_url": photo_url
        })

    except Exception as e:
        logger.error(f"Ошибка отправки утреннего фото: {e}")
        return JSONResponse({"status": "error", "message": str(e)})
