import os
import re
import logging
import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from upstash_redis import Redis
from tgbot.sheets.take_from_sheet import get_sheet, ID_WORKSHEET, add_user_to_sheet_safe

logger = logging.getLogger(__name__)

# ==============================
# Redis ключи
# ==============================
REDIS_KEY_USERS = "sheet_users"       # user_id -> name
REDIS_KEY_ALLOWED = "allowed_users"   # set of allowed user_ids
REDIS_KEY_EVENTS = "event_data"       # hash для событий

# ==============================
# Redis клиент
# ==============================
redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

router = Router()


# ==============================
# Конвертер ссылок Google Drive
# ==============================
def convert_drive_url(url: str) -> str:
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


# ==============================
# Загрузка пользователей в Redis (одним запросом)
# ==============================
def load_sheet_users_to_redis():
    logger.info("Загрузка пользователей из Google Sheets в Redis...")

    sheet = get_sheet(ID_WORKSHEET)
    if not sheet:
        logger.error("Не удалось получить лист ID")
        return

    try:
        records = sheet.get_all_records()
        if not records:
            logger.warning("В листе нет пользователей для загрузки")
            return

        pipe = redis.pipeline()
        pipe.delete(REDIS_KEY_USERS)

        for row in records:
            user_id = row.get("user_id")
            if not user_id:
                continue
            name = row.get("name")
            if not name:
                first_name = row.get("first_name") or ""
                last_name = row.get("last_name") or ""
                name = f"{first_name} {last_name}".strip() or "Unknown"

            pipe.hset(REDIS_KEY_USERS, str(user_id), name)

        pipe.exec()
        logger.info(f"В Redis загружено {len(records)} пользователей")

    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей в Redis: {e}")


# ==============================
# Загрузка allowed users в Redis
# ==============================
def load_allowed_users_to_redis():
    sheet = get_sheet("Добавление")
    if not sheet:
        logger.error("Лист 'Добавление' не найден")
        return

    try:
        data = sheet.get_all_records()
        pipe = redis.pipeline()
        pipe.delete(REDIS_KEY_ALLOWED)

        for row in data:
            user_id = row.get("id")
            if user_id:
                pipe.sadd(REDIS_KEY_ALLOWED, int(user_id))

        pipe.exec()
        logger.info(f"Allowed users загружены в Redis: {len(data)} записей")

    except Exception as e:
        logger.error(f"Ошибка загрузки allowed users: {e}")


# ==============================
# Загрузка событий в Redis (бал, инн, орк, инст)
# ==============================
def load_event_data_to_redis():
    sheet = get_sheet("Инфо")
    if not sheet:
        logger.error("Лист 'Инфо' недоступен для загрузки событий")
        return

    try:
        events_map = {
            "bal": ("J2", "J3"),
            "inn": ("J5", "J6"),
            "ork": ("J8", "J9"),
            "inst": ("J11", "J12")
        }

        pipe = redis.pipeline()
        pipe.delete(REDIS_KEY_EVENTS)

        for event, (text_cell, media_cell) in events_map.items():
            text = sheet.acell(text_cell).value or ""
            media_url = sheet.acell(media_cell).value or ""
            media_url = convert_drive_url(media_url)
            pipe.hset(REDIS_KEY_EVENTS, f"{event}_text", text)
            pipe.hset(REDIS_KEY_EVENTS, f"{event}_media", media_url)

        pipe.exec()
        logger.info("Данные событий загружены в Redis")

    except Exception as e:
        logger.error(f"Ошибка загрузки данных событий: {e}")


# ==============================
# Получение allowed user ids
# ==============================
def get_allowed_user_ids() -> set[int]:
    try:
        ids = redis.smembers(REDIS_KEY_ALLOWED)
        return {int(user_id) for user_id in ids}
    except Exception as e:
        logger.error(f"Ошибка get_allowed_user_ids из Redis: {e}")
        return set()


# ==============================
# Проверка пользователя
# ==============================
def is_user_in_sheet(user_id: int) -> bool:
    return redis.hexists(REDIS_KEY_USERS, str(user_id))


# ==============================
# Получение имени
# ==============================
def get_name(user_id: int, telegram_first_name: str) -> str:
    name = redis.hget(REDIS_KEY_USERS, str(user_id))
    if name:
        return name
    return telegram_first_name or "Unknown"


# ==============================
# Добавление пользователя
# ==============================
def add_user_to_sheet_and_redis(user_id: int, username: str, first_name: str, last_name: str):
    add_user_to_sheet_safe(user_id, username, first_name, last_name)
    full_name = f"{first_name} {last_name}".strip()
    if not full_name or full_name.lower() == "unknown unknown":
        full_name = first_name or "Unknown"
    redis.hset(REDIS_KEY_USERS, str(user_id), full_name)
    logger.info(f"Пользователь {username} ({user_id}) добавлен в Redis")


# ==============================
# Функции получения данных событий
# ==============================
def get_bal_data() -> tuple[str, str]:
    text = redis.hget(REDIS_KEY_EVENTS, "bal_text") or "Данные недоступны"
    media_url = redis.hget(REDIS_KEY_EVENTS, "bal_media") or ""
    return text, media_url

def get_inn_data() -> tuple[str, str]:
    text = redis.hget(REDIS_KEY_EVENTS, "inn_text") or "Данные недоступны"
    media_url = redis.hget(REDIS_KEY_EVENTS, "inn_media") or ""
    return text, media_url

def get_ork_data() -> tuple[str, str]:
    text = redis.hget(REDIS_KEY_EVENTS, "ork_text") or "Данные недоступны"
    media_url = redis.hget(REDIS_KEY_EVENTS, "ork_media") or ""
    return text, media_url

def get_inst_data() -> tuple[str, str]:
    text = redis.hget(REDIS_KEY_EVENTS, "inst_text") or "Данные недоступны"
    media_url = redis.hget(REDIS_KEY_EVENTS, "inst_media") or ""
    return text, media_url


# ==============================
# Обработка всех сообщений
# ==============================
@router.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"

    if not is_user_in_sheet(user_id):
        logger.info(f"Пользователь {username} ({user_id}) не найден, добавляем...")
        await asyncio.to_thread(
            add_user_to_sheet_and_redis,
            user_id,
            username,
            first_name,
            last_name
        )
        logger.info(f"Пользователь {username} ({user_id}) успешно добавлен")
    else:
        logger.info(f"Пользователь {username} ({user_id}) уже есть в списке")
