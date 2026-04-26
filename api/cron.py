"""
api/cron.py — все cron-эндпоинты в одном месте.

Защита: передавай заголовок  X-Cron-Secret: <значение CRON_SECRET из env>
в каждом задании на cron-jobs.org.
"""
import os
import time
import random
import asyncio
import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from tgbot import tgbot
from tgbot.sheets.gspread_client import get_gspread_client
from tgbot.handlers.bless import build_caption, create_bless_keyboard
from tgbot.redis.redis_cash import (
    redis,
    LAST_UPDATE_KEY,
    get_bless_data,
    load_users_to_redis,
    load_allowed_to_redis,
    load_all_data_to_redis,
    load_autosbor_to_redis,
    load_admins_to_redis,
)

logger = logging.getLogger(__name__)
router = APIRouter()

CRON_SECRET = os.getenv("CRON_SECRET", "")
CHAT_ID     = os.getenv("CHAT_ID")
SHEET_NAME  = os.getenv("SHEET_NAME")


# ==============================
# Защита cron-эндпоинтов
# ==============================
def verify_cron_secret(request: Request):
    """Проверяет заголовок X-Cron-Secret. Если CRON_SECRET не задан — пропускает всех."""
    if CRON_SECRET and request.headers.get("X-Cron-Secret") != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


# ==============================
# Refresh-задания (обновление Redis из Sheets)
# ==============================
async def _refresh(loader_func, label: str) -> JSONResponse:
    try:
        count = await asyncio.to_thread(loader_func)
        redis.set(LAST_UPDATE_KEY, int(time.time()))
        return JSONResponse({"status": "ok", "message": f"✅ {label} обновлены ({count})"})
    except Exception as e:
        logger.error(f"Ошибка refresh {label}: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


@router.get("/api/cron/refresh_users")
async def cron_refresh_users(request: Request):
    verify_cron_secret(request)
    return await _refresh(load_users_to_redis, "Пользователи")


@router.get("/api/cron/refresh_allowed")
async def cron_refresh_allowed(request: Request):
    verify_cron_secret(request)
    return await _refresh(load_allowed_to_redis, "Allowed users")


@router.get("/api/cron/refresh_all_data")
async def cron_refresh_all_data(request: Request):
    verify_cron_secret(request)
    return await _refresh(load_all_data_to_redis, "Events, Menu и Bot Commands")


@router.get("/api/cron/refresh_autosbor")
async def cron_refresh_autosbor(request: Request):
    verify_cron_secret(request)
    return await _refresh(load_autosbor_to_redis, "Автосбор")


@router.get("/api/cron/refresh_admins")
async def cron_refresh_admins(request: Request):
    verify_cron_secret(request)
    return await _refresh(load_admins_to_redis, "Админы")


# ==============================
# Bless
# ==============================
@router.get("/api/cron/bless")
async def cron_bless(request: Request):
    verify_cron_secret(request)
    try:
        if not CHAT_ID:
            return JSONResponse({"status": "error", "message": "CHAT_ID не задан"})

        _, photo   = get_bless_data()
        caption    = build_caption([], [])
        keyboard   = create_bless_keyboard()

        if photo:
            sent = await tgbot.bot.send_photo(
                chat_id=int(CHAT_ID), photo=photo, caption=caption, reply_markup=keyboard
            )
        else:
            sent = await tgbot.bot.send_message(
                chat_id=int(CHAT_ID), text=caption, reply_markup=keyboard
            )

        try:
            await tgbot.bot.pin_chat_message(chat_id=int(CHAT_ID), message_id=sent.message_id)
        except Exception:
            pass

        return JSONResponse({"status": "ok", "message": "✅ Bless сообщение отправлено"})
    except Exception as e:
        logger.error(f"Ошибка cron_bless: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


# ==============================
# Случайная отправка из листа Сохранения
# ==============================
@router.get("/api/cron/random_send")
async def cron_random_send(request: Request):
    verify_cron_secret(request)
    try:
        if not CHAT_ID:
            return JSONResponse({"status": "error", "message": "CHAT_ID не задан"})

        client  = get_gspread_client()
        sheet   = client.open(SHEET_NAME).worksheet("Сохранения")
        records = sheet.get_all_records()

        if not records:
            return JSONResponse({"status": "error", "message": "Таблица пустая"})

        record       = random.choice(records)
        name         = record.get("Имя", "Без названия")
        file_type_ru = str(record.get("Тип", "")).lower()
        file_id      = record.get("ID")

        if not file_id:
            return JSONResponse({"status": "error", "message": "Не найден ID в записи"})

        chat_id = int(CHAT_ID)

        if file_type_ru == "фото":
            await tgbot.bot.send_photo(chat_id=chat_id, photo=file_id, caption=name)
        elif file_type_ru == "видео":
            await tgbot.bot.send_video(chat_id=chat_id, video=file_id, caption=name)
        elif file_type_ru == "гиф":
            await tgbot.bot.send_animation(chat_id=chat_id, animation=file_id)
            await tgbot.bot.send_message(chat_id=chat_id, text=name)
        else:
            await tgbot.bot.send_document(chat_id=chat_id, document=file_id, caption=name)

        return JSONResponse({"status": "ok", "sent": name, "type": file_type_ru})
    except Exception as e:
        logger.error(f"Ошибка random_send: {e}")
        return JSONResponse({"status": "error", "message": str(e)})
