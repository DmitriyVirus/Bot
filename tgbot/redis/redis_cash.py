import os
import logging
import asyncio
from aiogram import Router, types
from aiogram.filters import Command, F
from upstash_redis import Redis
from tgbot.sheets.take_from_sheet import get_sheet, ID_WORKSHEET, add_user_to_sheet_safe

logger = logging.getLogger(__name__)

REDIS_KEY = "sheet_users"

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

router = Router()


# ==============================
# Загрузка пользователей в Redis
# ==============================
def load_sheet_users_to_redis():
    """
    Загружает все user_id из листа ID в Redis (SET).
    Вызывается один раз при старте бота.
    """
    logger.info("Загрузка пользователей из Google Sheets в Redis...")

    sheet = get_sheet(ID_WORKSHEET)
    if not sheet:
        logger.error("Не удалось получить лист ID")
        return

    try:
        records = sheet.get_all_records()
        user_ids = [str(row["user_id"]) for row in records if row.get("user_id")]

        if not user_ids:
            logger.warning("В листе нет user_id")
            return

        # очищаем старые данные
        redis.delete(REDIS_KEY)

        # загружаем новые
        redis.sadd(REDIS_KEY, *user_ids)

        logger.info(f"В Redis загружено {len(user_ids)} пользователей")
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей в Redis: {e}")


# ==============================
# Проверка пользователя
# ==============================
def is_user_in_sheet(user_id: int) -> bool:
    """
    Проверяет, есть ли user_id в Redis.
    """
    return redis.sismember(REDIS_KEY, str(user_id))


# ==============================
# Добавление нового пользователя
# ==============================
def add_user_to_sheet_and_redis(user_id: int, username: str, first_name: str, last_name: str):
    """
    Добавляет пользователя в Google Sheets и сразу в Redis.
    """
    # Добавляем в Google Sheets
    add_user_to_sheet_safe(user_id, username, first_name, last_name)

    # Добавляем в Redis
    redis.sadd(REDIS_KEY, str(user_id))
    logger.info(f"Пользователь {username} ({user_id}) добавлен в Redis")


# ==============================
# Команда /exist
# ==============================
@router.message(Command("exist"))
async def check_exist(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"

    if is_user_in_sheet(user_id):
        await message.answer("✅ Вы есть в таблице.")
    else:
        # Если пользователя нет — добавляем в Google Sheets + Redis
        await message.answer("❌ Вас нет в таблице, добавляем...")
        await asyncio.to_thread(add_user_to_sheet_and_redis, user_id, username, first_name, last_name)
        await message.answer("✅ Пользователь добавлен!")


# ==============================
# Обработка всех сообщений (кроме команд)
# ==============================
@router.message(F.text & ~F.text.startswith("/"))
async def handle_non_command_messages(message: types.Message):
    """
    Проверяем пользователя в Redis при получении любого сообщения,
    кроме команд. Если пользователя нет — добавляем в Google Sheets и Redis.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or "Unknown"

    # Проверяем Redis
    if not is_user_in_sheet(user_id):
        logger.info(f"Пользователь {username} ({user_id}) не найден, добавляем...")
        await asyncio.to_thread(add_user_to_sheet_and_redis, user_id, username, first_name, last_name)
        logger.info(f"Пользователь {username} ({user_id}) успешно добавлен")
    else:
        logger.info(f"Пользователь {username} ({user_id}) уже есть в списке")
