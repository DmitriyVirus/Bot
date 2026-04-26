import os
import re
import time
import json
import logging
import asyncio
from upstash_redis import Redis
from aiogram import Router, types
from tgbot.sheets.take_from_sheet import get_sheet, ID_WORKSHEET, add_user_to_sheet_safe

logger = logging.getLogger(__name__)

# ==============================
# Redis ключи
# ==============================
REDIS_KEY_USERS    = "sheet_users"
REDIS_KEY_ALLOWED  = "allowed_users"
REDIS_KEY_AUTOSBOR = "autosbor_data"
REDIS_KEY_ADMINS   = "admins_data"
REDIS_KEY_BOT_CMD  = "bot_cmd"
REDIS_KEY_BOT_DEB_CMD = "bot_deb_cmd"
REDIS_KEY_ALL_DATA = "all_data"
LAST_UPDATE_KEY    = "last_update_redis"

# ==============================
# Redis клиент
# ==============================
redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

router = Router()


async def refresh_redis():
    """Основная функция обновления Redis."""
    await asyncio.to_thread(load_all_to_redis)
    redis.set(LAST_UPDATE_KEY, int(time.time()))
    return "✅ Redis успешно обновлён!"


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
# Универсальный геттер данных из all_data
# Заменяет ~10 одинаковых функций get_*_data()
# ==============================
def get_event_data(key: str) -> tuple[str, str]:
    """
    Получает текст и медиа-ссылку для любого ключа из all_data.
    Пример: get_event_data("bal") → (text, media_url)
    """
    text      = redis.hget(REDIS_KEY_ALL_DATA, f"{key}_text")  or "Данные недоступны"
    media_url = redis.hget(REDIS_KEY_ALL_DATA, f"{key}_media") or ""
    return text, media_url


# Алиасы для совместимости с handlers (не дублируют логику — только вызывают универсальную функцию)
def get_bal_data()    -> tuple[str, str]: return get_event_data("bal")
def get_inn_data()    -> tuple[str, str]: return get_event_data("inn")
def get_ork_data()    -> tuple[str, str]: return get_event_data("ork")
def get_inst_data()   -> tuple[str, str]: return get_event_data("inst")
def get_freya_data()  -> tuple[str, str]: return get_event_data("freya")
def get_ramona_data() -> tuple[str, str]: return get_event_data("ramona")
def get_bless_data()  -> tuple[str, str]: return get_event_data("bless")
def get_fu_data()     -> tuple[str, str]: return get_event_data("fu")
def get_nakol_data()  -> tuple[str, str]: return get_event_data("nakol")
def get_klaar_data()  -> tuple[str, str]: return get_event_data("klaar")
def get_kris_data()   -> tuple[str, str]: return get_event_data("kris")


# ==============================
# Геттеры текстовых полей
# ==============================
def get_hello()            -> str: return redis.hget(REDIS_KEY_ALL_DATA, "hello_text")  or ""
def get_about_bot()        -> str: return redis.hget(REDIS_KEY_ALL_DATA, "about_text")  or ""
def get_cmd_info()         -> str: return redis.hget(REDIS_KEY_ALL_DATA, "cmd_info")    or ""
def get_hello_image()      -> str: return redis.hget(REDIS_KEY_ALL_DATA, "hello_image") or ""
def get_about_bot_image()  -> str: return redis.hget(REDIS_KEY_ALL_DATA, "about_image") or ""
def get_welcome()          -> str: return redis.hget(REDIS_KEY_ALL_DATA, "welcome_text") or ""


def get_bot_commands() -> list[str]:
    try:
        return redis.lrange(REDIS_KEY_BOT_CMD, 0, -1) or ["Команды недоступны"]
    except Exception as e:
        logger.error(f"Ошибка чтения команд бота из Redis: {e}")
        return ["Команды недоступны"]


def get_bot_deb_cmd() -> list[str]:
    try:
        return redis.lrange(REDIS_KEY_BOT_DEB_CMD, 0, -1) or ["Команды недоступны"]
    except Exception as e:
        logger.error(f"Ошибка чтения debug-команд из Redis: {e}")
        return ["Команды недоступны"]


# ==============================
# Геттеры пользователей
# ==============================
def get_name_username_dict() -> dict[str, str]:
    try:
        all_users = redis.hgetall(REDIS_KEY_USERS)
        return {
            data["name"].strip(): data["username"].strip()
            for user_json in all_users.values()
            if (data := json.loads(user_json)).get("name") and data.get("username")
        }
    except Exception as e:
        logger.error(f"Ошибка при получении данных name -> username из Redis: {e}")
        return {}


def get_allowed_user_ids() -> set[int]:
    try:
        return {int(uid) for uid in redis.smembers(REDIS_KEY_ALLOWED)}
    except Exception as e:
        logger.error(f"Ошибка get_allowed_user_ids из Redis: {e}")
        return set()


def get_admins_records() -> set[int]:
    try:
        return {int(uid) for uid in redis.smembers(REDIS_KEY_ADMINS)}
    except Exception as e:
        logger.error(f"Ошибка получения админов из Redis: {e}")
        return set()


def is_user_in_sheet(user_id: int) -> bool:
    return redis.hexists(REDIS_KEY_USERS, str(user_id))


def get_name(user_id: int, telegram_first_name: str) -> str:
    user_json = redis.hget(REDIS_KEY_USERS, str(user_id))
    if user_json:
        try:
            return json.loads(user_json).get("name") or telegram_first_name or "Unknown"
        except Exception:
            return telegram_first_name or "Unknown"
    return telegram_first_name or "Unknown"


# ==============================
# Автосбор
# ==============================
def get_column_data_from_autosbor(column_index: int, row_width: int = 10) -> list[str]:
    try:
        all_values = redis.lrange("autosbor_data", 0, -1)
        all_values = [v.decode() if isinstance(v, bytes) else v for v in all_values]

        if not all_values or column_index <= 0 or column_index > row_width:
            return []

        return [
            all_values[i]
            for i in range(column_index - 1, len(all_values), row_width)
            if all_values[i] != "1"
        ]
    except Exception as e:
        logger.error(f"Ошибка при get_column_data_from_autosbor из Redis: {e}")
        return []


# ==============================
# Добавление пользователя
# ==============================
def add_user_to_sheet_and_redis(user_id: int, username: str, first_name: str, last_name: str):
    add_user_to_sheet_safe(user_id, username, first_name, last_name)
    full_name = f"{first_name} {last_name}".strip() or "Unknown"
    redis.hset(
        REDIS_KEY_USERS,
        str(user_id),
        json.dumps({"user_id": int(user_id), "name": full_name, "username": username})
    )
    logger.info(f"Пользователь {username} ({user_id}) добавлен в Redis")


# ==============================
# Обработка новых сообщений (авто-регистрация)
# ==============================
@router.message()
async def handle_all_messages(message: types.Message):
    user_id   = message.from_user.id
    username   = message.from_user.username   or "Unknown"
    first_name = message.from_user.first_name or "Unknown"
    last_name  = message.from_user.last_name  or "Unknown"

    if not is_user_in_sheet(user_id):
        logger.info(f"Пользователь {username} ({user_id}) не найден, добавляем...")
        await asyncio.to_thread(add_user_to_sheet_and_redis, user_id, username, first_name, last_name)
        logger.info(f"Пользователь {username} ({user_id}) успешно добавлен")
    else:
        logger.info(f"Пользователь {username} ({user_id}) уже есть в списке")


# ==============================
# Загрузка данных в Redis
# ==============================
def load_users_to_redis() -> int:
    sheet_users = get_sheet(ID_WORKSHEET)
    if not sheet_users:
        logger.warning("Лист пользователей не найден")
        return 0
    records = sheet_users.get_all_records()
    if not records:
        return 0

    pipe = redis.pipeline()
    pipe.delete(REDIS_KEY_USERS)
    for row in records:
        user_id = row.get("user_id")
        if not user_id:
            continue
        name     = row.get("name") or f"{row.get('first_name','')} {row.get('last_name','')}".strip() or "Unknown"
        username = row.get("username") or "Unknown"
        pipe.hset(REDIS_KEY_USERS, str(user_id), json.dumps({"user_id": int(user_id), "name": name, "username": username}))
    pipe.exec()
    logger.info(f"Загружено пользователей: {len(records)}")
    return len(records)


def load_allowed_to_redis() -> int:
    sheet_allowed = get_sheet("Добавление")
    if not sheet_allowed:
        logger.warning("Лист 'Добавление' не найден")
        return 0
    records = sheet_allowed.get_all_records()

    pipe = redis.pipeline()
    pipe.delete(REDIS_KEY_ALLOWED)
    for row in records:
        user_id = row.get("id")
        if user_id:
            pipe.sadd(REDIS_KEY_ALLOWED, int(user_id))
    pipe.exec()
    logger.info(f"Allowed users загружены: {len(records)}")
    return len(records)


def load_all_data_to_redis() -> int:
    sheet_info = get_sheet("Инфо")
    if not sheet_info:
        logger.warning("Лист 'Инфо' не найден")
        return 0

    pipe = redis.pipeline()
    pipe.delete(REDIS_KEY_ALL_DATA)

    # Events — используем тот же паттерн key: (text_cell, media_cell)
    events_map = {
        "bal":    ("J2",  "J3"),
        "inn":    ("J5",  "J6"),
        "ork":    ("J8",  "J9"),
        "inst":   ("J11", "J12"),
        "freya":  ("J14", "J15"),
        "ramona": ("J17", "J18"),
        "bless":  ("J20", "J21"),
    }
    media_map = {
        "fu":    ("I2",  "I3"),
        "nakol": ("I5",  "I6"),
        "klaar": ("I8",  "I9"),
        "kris":  ("I11", "I12"),
    }

    for key, (text_cell, media_cell) in {**events_map, **media_map}.items():
        text      = sheet_info.acell(text_cell).value  or ""
        media_url = convert_drive_url(sheet_info.acell(media_cell).value or "")
        pipe.hset(REDIS_KEY_ALL_DATA, f"{key}_text",  text)
        pipe.hset(REDIS_KEY_ALL_DATA, f"{key}_media", media_url)

    # Menu
    welcome_text = "\n".join([r[0] for r in sheet_info.get("A2:A19") if r])
    hello_text   = "\n".join([r[0] for r in sheet_info.get("B2:B19") if r])
    about_text   = "\n".join([r[0] for r in sheet_info.get("C2:C19") if r])
    cmd_info     = "\n".join([r[0] for r in sheet_info.get("D2:D19") if r])
    hello_img    = convert_drive_url(sheet_info.acell("B20").value or "")
    about_img    = convert_drive_url(sheet_info.acell("C20").value or "")

    pipe.hset(REDIS_KEY_ALL_DATA, "welcome_text", welcome_text)
    pipe.hset(REDIS_KEY_ALL_DATA, "hello_text",   hello_text)
    pipe.hset(REDIS_KEY_ALL_DATA, "about_text",   about_text)
    pipe.hset(REDIS_KEY_ALL_DATA, "cmd_info",     cmd_info)
    pipe.hset(REDIS_KEY_ALL_DATA, "hello_image",  hello_img)
    pipe.hset(REDIS_KEY_ALL_DATA, "about_image",  about_img)
    pipe.exec()
    logger.info("Events + Menu загружены в all_data")

    # Bot Commands
    try:
        headers        = sheet_info.row_values(1)
        cmd_index      = headers.index("cmd_bot") + 1
        text_index     = headers.index("cmd_bot_text") + 1
        deb_cmd_index  = headers.index("cmd_bot_deb") + 1
        deb_text_index = headers.index("cmd_bot_deb_text") + 1

        cmd_values     = sheet_info.col_values(cmd_index)[1:]
        text_values    = sheet_info.col_values(text_index)[1:]
        deb_cmd_values = sheet_info.col_values(deb_cmd_index)[1:]
        deb_text_values= sheet_info.col_values(deb_text_index)[1:]

        bot_cmd_list     = [f"{c} — {t}" if t else c for c, t in zip(cmd_values,     text_values)     if c.strip()]
        bot_deb_cmd_list = [f"{c} — {t}" if t else c for c, t in zip(deb_cmd_values, deb_text_values) if c.strip()]

        pipe_cmd = redis.pipeline()
        pipe_cmd.delete(REDIS_KEY_BOT_CMD)
        pipe_cmd.delete(REDIS_KEY_BOT_DEB_CMD)
        if bot_cmd_list:     pipe_cmd.rpush(REDIS_KEY_BOT_CMD,     *bot_cmd_list)
        if bot_deb_cmd_list: pipe_cmd.rpush(REDIS_KEY_BOT_DEB_CMD, *bot_deb_cmd_list)
        pipe_cmd.exec()
        logger.info(f"Команды загружены: {len(bot_cmd_list)} обычных, {len(bot_deb_cmd_list)} debug")
    except Exception as e:
        logger.error(f"Ошибка загрузки bot_cmd: {e}")

    return 1


def load_autosbor_to_redis() -> int:
    sheet_autosbor = get_sheet("Автосбор")
    if not sheet_autosbor:
        logger.warning("Лист 'Автосбор' не найден")
        return 0
    all_values = sheet_autosbor.get_all_values()
    flat_list  = [cell.strip() if cell.strip() else "1" for row in all_values for cell in row]

    pipe = redis.pipeline()
    pipe.delete(REDIS_KEY_AUTOSBOR)
    if flat_list:
        pipe.rpush(REDIS_KEY_AUTOSBOR, *flat_list)
    pipe.exec()
    logger.info(f"Автосбор загружен ({len(flat_list)} элементов)")
    return len(flat_list)


def load_admins_to_redis() -> int:
    sheet_admins = get_sheet("Админы")
    if not sheet_admins:
        logger.warning("Лист 'Админы' не найден")
        return 0
    records = sheet_admins.get_all_records()

    pipe = redis.pipeline()
    pipe.delete(REDIS_KEY_ADMINS)
    for row in records:
        admin_id = row.get("id")
        if admin_id:
            pipe.sadd(REDIS_KEY_ADMINS, int(admin_id))
    pipe.exec()
    logger.info(f"Админы загружены ({len(records)} записей)")
    return len(records)


def load_all_to_redis():
    logger.info("=== Загрузка всех данных в Redis (full) ===")
    load_users_to_redis()
    load_allowed_to_redis()
    load_all_data_to_redis()
    load_autosbor_to_redis()
    load_admins_to_redis()
    logger.info("=== Загрузка всех данных завершена ===")
