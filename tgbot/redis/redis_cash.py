import os
import logging
from aiogram import Router, types
from aiogram.filters import Command
from upstash_redis import Redis
from tgbot.sheets.take_from_sheet import get_sheet, ID_WORKSHEET

logger = logging.getLogger(__name__)

REDIS_KEY = "sheet_users"

# Инициализация Redis (REST API)
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
    Синхронная функция, вызывается при старте бота.
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
    """Проверяет, есть ли user_id в Redis."""
    return redis.sismember(REDIS_KEY, str(user_id))


# ==============================
# Команда /exist
# ==============================
@router.message(Command("exist"))
async def check_exist(message: types.Message):
    user_id = message.from_user.id
    exists = is_user_in_sheet(user_id)  # Синхронно через Redis

    if exists:
        await message.answer("✅ Вы есть в таблице.")
    else:
        await message.answer("❌ Вас нет в таблице.")
