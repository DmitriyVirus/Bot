import os
import logging
import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from upstash_redis import Redis
from tgbot.sheets.take_from_sheet import get_sheet, ID_WORKSHEET, add_user_to_sheet_safe

logger = logging.getLogger(__name__)

# Один ключ — один hash: user_id -> name
REDIS_KEY_USERS = "sheet_users"

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

router = Router()


# ==============================
# Загрузка пользователей в Redis (ОДНИМ запросом)
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

        # очищаем старый hash
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

        # 🔥 один HTTP вызов вместо тысячи
        pipe.exec()

        logger.info(f"В Redis загружено {len(records)} пользователей")

    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей в Redis: {e}")


# ==============================
# Проверка пользователя (через hash)
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
    # Добавляем в Google Sheets
    add_user_to_sheet_safe(user_id, username, first_name, last_name)

    # Формируем имя
    full_name = f"{first_name} {last_name}".strip()
    if not full_name or full_name.lower() == "unknown unknown":
        full_name = first_name or "Unknown"

    # ОДИН запрос в Redis
    redis.hset(REDIS_KEY_USERS, str(user_id), full_name)

    logger.info(f"Пользователь {username} ({user_id}) добавлен в Redis")

def load_allowed_users_to_redis():

    sheet = get_sheet("Добавление")
    if not sheet:
        return

    try:
        data = sheet.get_all_records()

        r.delete("allowed_users")  # очищаем перед загрузкой

        for row in data:
            if "id" in row and row["id"]:
                r.sadd("allowed_users", int(row["id"]))

        logger.info("Allowed users загружены в Redis")

    except Exception as e:
        logger.error(f"Ошибка загрузки allowed users: {e}")

def get_allowed_user_ids():
    try:
        ids = r.smembers("allowed_users")
        return {int(user_id) for user_id in ids}
    except Exception as e:
        logger.error(f"Ошибка get_allowed_user_ids из Redis: {e}")
        return set()


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
