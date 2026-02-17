import os
import logging
import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from upstash_redis import Redis
from tgbot.sheets.take_from_sheet import get_sheet, ID_WORKSHEET, add_user_to_sheet_safe

logger = logging.getLogger(__name__)

# Множество для проверки наличия в таблице
REDIS_KEY = "sheet_users"
# Хеш для хранения user_id → name
REDIS_KEY_USERS = "sheet_users_names"

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

router = Router()


# ==============================
# Загрузка пользователей в Redis (множество и хеш)
# ==============================
def load_sheet_users_to_redis():
    logger.info("Загрузка пользователей из Google Sheets в Redis...")
    sheet = get_sheet(ID_WORKSHEET)
    if not sheet:
        logger.error("Не удалось получить лист ID")
        return
    try:
        records = sheet.get_all_records()
        user_ids = []
        user_mapping = {}
        for row in records:
            uid = row.get("user_id")
            name = row.get("name", "").strip() or "Unknown"
            if uid:
                user_ids.append(str(uid))
                user_mapping[str(uid)] = name

        if not user_ids:
            logger.warning("В листе нет пользователей для загрузки")
            return

        # Множество для проверки наличия
        redis.delete(REDIS_KEY)
        redis.sadd(REDIS_KEY, *user_ids)

        # Хеш для имен
        redis.delete(REDIS_KEY_USERS)
        redis.hset(REDIS_KEY_USERS, user_mapping)

        logger.info(f"В Redis загружено {len(user_ids)} пользователей")
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей в Redis: {e}")


# ==============================
# Проверка пользователя в множестве
# ==============================
def is_user_in_sheet(user_id: int) -> bool:
    return redis.sismember(REDIS_KEY, str(user_id))


# ==============================
# Получение имени пользователя (хеш)
# ==============================
def get_name(user_id: int, telegram_first_name: str) -> str:
    """Берём имя пользователя из Redis или Telegram"""
    name = redis.hget(REDIS_KEY_USERS, str(user_id))
    if name:
        return name
    return telegram_first_name or "Unknown"


# ==============================
# Добавление пользователя в Google Sheets и Redis
# ==============================
def add_user_to_sheet_and_redis(user_id: int, username: str, first_name: str, last_name: str):
    # Добавляем в Google Sheets
    add_user_to_sheet_safe(user_id, username, first_name, last_name)

    # Добавляем в множество
    redis.sadd(REDIS_KEY, str(user_id))

    # Добавляем в хеш
    full_name = f"{first_name} {last_name}".strip()
    if not full_name or full_name.lower() == "unknown unknown":
        full_name = first_name or "Unknown"
    redis.hset(REDIS_KEY_USERS, str(user_id), full_name)

    logger.info(f"Пользователь {username} ({user_id}) добавлен в Redis")


# ==============================
# Обработка всех сообщений
# ==============================
@router.message()
async def handle_all_messages(message: types.Message):
    """
    Обрабатывает все сообщения.
    Проверяем пользователя в Redis; если нет — добавляем в Google Sheets и Redis.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"

    if not is_user_in_sheet(user_id):
        logger.info(f"Пользователь {username} ({user_id}) не найден, добавляем...")
        await asyncio.to_thread(add_user_to_sheet_and_redis, user_id, username, first_name, last_name)
        logger.info(f"Пользователь {username} ({user_id}) успешно добавлен")
    else:
        logger.info(f"Пользователь {username} ({user_id}) уже есть в списке")
