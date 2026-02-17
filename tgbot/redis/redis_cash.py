import os
import re
import json
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
REDIS_KEY_USERS = "sheet_users"       # user_id -> JSON {name, username, user_id}
REDIS_KEY_ALLOWED = "allowed_users"   # set of allowed user_ids
REDIS_KEY_EVENTS = "event_data"       # hash для событий
REDIS_KEY_AUTOSBOR = "autosbor_data"  # список всех значений из листа "Автосбор"


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
# Загрузка пользователей в Redis (одним запросом, JSON)
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

            # Формируем name
            name = row.get("name")
            if not name:
                first_name = row.get("first_name") or ""
                last_name = row.get("last_name") or ""
                name = f"{first_name} {last_name}".strip() or "Unknown"

            # Берём username из таблицы
            username = row.get("username") or "Unknown"

            # JSON объект
            user_json = json.dumps({
                "user_id": int(user_id),
                "name": name,
                "username": username
            })

            pipe.hset(REDIS_KEY_USERS, str(user_id), user_json)

        pipe.exec()
        logger.info(f"В Redis загружено {len(records)} пользователей")

    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей в Redis: {e}")


# ==============================
# Получение словаря name -> username
# ==============================
def get_name_username_dict() -> dict[str, str]:
    """
    Возвращает словарь:
    ключ = name (например 'Дмитрий(маКароноВирус)')
    значение = username Telegram (например 'DDestopia')
    Алиасы игнорируются.
    Данные берутся из Redis, а не из Google Sheets.
    """
    try:
        all_users = redis.hgetall(REDIS_KEY_USERS)
        name_username = {}
        for user_json in all_users.values():
            try:
                data = json.loads(user_json)
                name = data.get("name")
                username = data.get("username")
                if name and username:
                    name_username[name.strip()] = username.strip()
            except Exception:
                continue
        return name_username
    except Exception as e:
        logger.error(f"Ошибка при получении данных name -> username из Redis: {e}")
        return {}

# ==============================
# Остальной функционал
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


def get_allowed_user_ids() -> set[int]:
    try:
        ids = redis.smembers(REDIS_KEY_ALLOWED)
        return {int(user_id) for user_id in ids}
    except Exception as e:
        logger.error(f"Ошибка get_allowed_user_ids из Redis: {e}")
        return set()


def is_user_in_sheet(user_id: int) -> bool:
    return redis.hexists(REDIS_KEY_USERS, str(user_id))


def get_name(user_id: int, telegram_first_name: str) -> str:
    user_json = redis.hget(REDIS_KEY_USERS, str(user_id))
    if user_json:
        try:
            data = json.loads(user_json)
            return data.get("name") or telegram_first_name or "Unknown"
        except Exception:
            return telegram_first_name or "Unknown"
    return telegram_first_name or "Unknown"


def add_user_to_sheet_and_redis(user_id: int, username: str, first_name: str, last_name: str):
    add_user_to_sheet_safe(user_id, username, first_name, last_name)
    full_name = f"{first_name} {last_name}".strip() or "Unknown"
    user_json = json.dumps({
        "user_id": int(user_id),
        "name": full_name,
        "username": username
    })
    redis.hset(REDIS_KEY_USERS, str(user_id), user_json)
    logger.info(f"Пользователь {username} ({user_id}) добавлен в Redis")


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
# Загрузка данных Автосбор в Redis
# ==============================
def load_autosbor_to_redis():
    """
    Загружает данные из листа 'Автосбор' в Redis.
    Все значения складываются в один список.
    Пустые ячейки заменяются на маркер '1'.
    """
    sheet = get_sheet("Автосбор")
    if not sheet:
        logger.error("Лист 'Автосбор' не найден")
        return

    try:
        all_values = sheet.get_all_values()  # получаем все строки
        flat_list = []

        for row in all_values:
            for cell in row:
                value = cell.strip() if cell.strip() else "1"
                flat_list.append(value)

        # Сохраняем в Redis через pipeline
        pipe = redis.pipeline()
        pipe.delete(REDIS_KEY_AUTOSBOR)
        if flat_list:
            pipe.rpush(REDIS_KEY_AUTOSBOR, *flat_list)
        pipe.exec()

        logger.info(f"Данные 'Автосбор' загружены в Redis ({len(flat_list)} элементов)")

    except Exception as e:
        logger.error(f"Ошибка загрузки 'Автосбор' в Redis: {e}")


# ==============================
# Получение колонки из Redis
# ==============================
def get_column_data_from_autosbor(column_index: int, row_width: int = 10) -> list[str]:
    """
    Возвращает список значений из колонки column_index (1 = первый столбец)
    row_width: количество столбцов в таблице
    Пустые ячейки возвращаются как "".
    """
    try:
        all_values = redis.lrange(REDIS_KEY_AUTOSBOR, 0, -1)
        if not all_values or column_index <= 0 or column_index > row_width:
            return []

        col_data = []
        for i in range(column_index - 1, len(all_values), row_width):
            value = all_values[i]
            if value == "1":  # маркер пустой ячейки
                value = ""
            col_data.append(value)

        return col_data

    except Exception as e:
        logger.error(f"Ошибка при get_column_data_from_autosbor из Redis: {e}")
        return []



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
