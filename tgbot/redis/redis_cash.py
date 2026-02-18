import os
import re
import json
import logging
import asyncio
from aiogram import Router, types
from upstash_redis import Redis
from tgbot.sheets.take_from_sheet import get_sheet, ID_WORKSHEET, add_user_to_sheet_safe

logger = logging.getLogger(__name__)


# ==============================
# Redis ключи
# ==============================
REDIS_KEY_USERS = "sheet_users"
REDIS_KEY_ALLOWED = "allowed_users"
REDIS_KEY_EVENTS = "event_data"
REDIS_KEY_AUTOSBOR = "autosbor_data"
REDIS_KEY_MENU = "menu_data"
REDIS_KEY_ADMINS = "admins_data"
REDIS_KEY_BOT_CMD = "bot_cmd"
REDIS_KEY_BOT_DEB_CMD = "bot_deb_cmd"


# ==============================
# Redis клиент
# ==============================
redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

router = Router()


# ============================================================
# Redis helpers (универсальные)
# ============================================================

def redis_replace_set(key: str, values: list[int]):
    pipe = redis.pipeline()
    pipe.delete(key)
    if values:
        pipe.sadd(key, *values)
    pipe.exec()


def redis_replace_list(key: str, values: list[str]):
    pipe = redis.pipeline()
    pipe.delete(key)
    if values:
        pipe.rpush(key, *values)
    pipe.exec()


def redis_replace_hash(key: str, mapping: dict):
    pipe = redis.pipeline()
    pipe.delete(key)
    if mapping:
        pipe.hset(key, mapping=mapping)
    pipe.exec()


# ==============================
# Конвертер ссылок Google Drive
# ==============================
def convert_drive_url(url: str) -> str:
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


# ============================================================
# USERS
# ============================================================

def load_sheet_users_to_redis():
    sheet = get_sheet(ID_WORKSHEET)
    if not sheet:
        logger.error("Не удалось получить лист ID")
        return

    try:
        records = sheet.get_all_records()
        pipe = redis.pipeline()
        pipe.delete(REDIS_KEY_USERS)

        for row in records:
            user_id = row.get("user_id")
            if not user_id:
                continue

            name = row.get("name")
            if not name:
                first = row.get("first_name") or ""
                last = row.get("last_name") or ""
                name = f"{first} {last}".strip() or "Unknown"

            username = row.get("username") or "Unknown"

            pipe.hset(
                REDIS_KEY_USERS,
                str(user_id),
                json.dumps({
                    "user_id": int(user_id),
                    "name": name,
                    "username": username
                })
            )

        pipe.exec()
        logger.info(f"Пользователи загружены: {len(records)}")

    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей: {e}")


def get_name_username_dict() -> dict[str, str]:
    try:
        all_users = redis.hgetall(REDIS_KEY_USERS)
        result = {}
        for user_json in all_users.values():
            try:
                data = json.loads(user_json)
                if data.get("name") and data.get("username"):
                    result[data["name"].strip()] = data["username"].strip()
            except Exception:
                continue
        return result
    except Exception as e:
        logger.error(f"Ошибка получения name->username: {e}")
        return {}


def is_user_in_sheet(user_id: int) -> bool:
    return redis.hexists(REDIS_KEY_USERS, str(user_id))


def get_name(user_id: int, telegram_first_name: str) -> str:
    user_json = redis.hget(REDIS_KEY_USERS, str(user_id))
    if user_json:
        try:
            data = json.loads(user_json)
            return data.get("name") or telegram_first_name or "Unknown"
        except Exception:
            pass
    return telegram_first_name or "Unknown"


def add_user_to_sheet_and_redis(user_id, username, first_name, last_name):
    add_user_to_sheet_safe(user_id, username, first_name, last_name)
    full_name = f"{first_name} {last_name}".strip() or "Unknown"

    redis.hset(
        REDIS_KEY_USERS,
        str(user_id),
        json.dumps({
            "user_id": int(user_id),
            "name": full_name,
            "username": username
        })
    )


# ============================================================
# ALLOWED + ADMINS (объединённая логика)
# ============================================================

def load_allowed_users_to_redis():
    sheet = get_sheet("Добавление")
    if not sheet:
        return
    data = sheet.get_all_records()
    ids = [int(r["id"]) for r in data if r.get("id")]
    redis_replace_set(REDIS_KEY_ALLOWED, ids)


def load_admins_to_redis():
    sheet = get_sheet("Админы")
    if not sheet:
        return
    data = sheet.get_all_records()
    ids = [int(r["id"]) for r in data if r.get("id")]
    redis_replace_set(REDIS_KEY_ADMINS, ids)


def get_allowed_user_ids() -> set[int]:
    try:
        return {int(x) for x in redis.smembers(REDIS_KEY_ALLOWED)}
    except Exception:
        return set()


def get_admins_records() -> set[int]:
    try:
        return {int(x) for x in redis.smembers(REDIS_KEY_ADMINS)}
    except Exception:
        return set()


# ============================================================
# EVENTS
# ============================================================

def load_event_data_to_redis():
    sheet = get_sheet("Инфо")
    if not sheet:
        return

    events_map = {
        "bal": ("J2", "J3"),
        "inn": ("J5", "J6"),
        "ork": ("J8", "J9"),
        "inst": ("J11", "J12")
    }

    data = {}

    for event, (text_cell, media_cell) in events_map.items():
        text = sheet.acell(text_cell).value or ""
        media = convert_drive_url(sheet.acell(media_cell).value or "")
        data[f"{event}_text"] = text
        data[f"{event}_media"] = media

    redis_replace_hash(REDIS_KEY_EVENTS, data)


def get_bal_data() -> tuple[str, str]:
    return (
        redis.hget(REDIS_KEY_EVENTS, "bal_text") or "Данные недоступны",
        redis.hget(REDIS_KEY_EVENTS, "bal_media") or ""
    )


def get_inn_data() -> tuple[str, str]:
    return (
        redis.hget(REDIS_KEY_EVENTS, "inn_text") or "Данные недоступны",
        redis.hget(REDIS_KEY_EVENTS, "inn_media") or ""
    )


def get_ork_data() -> tuple[str, str]:
    return (
        redis.hget(REDIS_KEY_EVENTS, "ork_text") or "Данные недоступны",
        redis.hget(REDIS_KEY_EVENTS, "ork_media") or ""
    )


def get_inst_data() -> tuple[str, str]:
    return (
        redis.hget(REDIS_KEY_EVENTS, "inst_text") or "Данные недоступны",
        redis.hget(REDIS_KEY_EVENTS, "inst_media") or ""
    )


# ============================================================
# AUTOSBOR
# ============================================================

def load_autosbor_to_redis():
    sheet = get_sheet("Автосбор")
    if not sheet:
        return

    flat_list = []
    for row in sheet.get_all_values():
        for cell in row:
            flat_list.append(cell.strip() if cell.strip() else "1")

    redis_replace_list(REDIS_KEY_AUTOSBOR, flat_list)


def get_column_data_from_autosbor(column_index: int, row_width: int = 10) -> list[str]:
    try:
        all_values = redis.lrange(REDIS_KEY_AUTOSBOR, 0, -1)
        if not all_values:
            return []

        result = []
        for i in range(column_index - 1, len(all_values), row_width):
            val = all_values[i]
            result.append("" if val == "1" else val)

        return result
    except Exception:
        return []


# ============================================================
# MENU
# ============================================================

def load_menu_data_to_redis():
    sheet = get_sheet("Инфо")
    if not sheet:
        return

    data = {
        "hello_text": "\n".join([r[0] for r in sheet.get("B2:B19") if r]),
        "about_text": "\n".join([r[0] for r in sheet.get("C2:C19") if r]),
        "cmd_info": "\n".join([r[0] for r in sheet.get("D2:D19") if r]),
        "hello_image": convert_drive_url(sheet.acell("B20").value or ""),
        "about_image": convert_drive_url(sheet.acell("C20").value or "")
    }

    redis_replace_hash(REDIS_KEY_MENU, data)


def get_hello():
    return redis.hget(REDIS_KEY_MENU, "hello_text") or ""


def get_about_bot():
    return redis.hget(REDIS_KEY_MENU, "about_text") or ""


def get_cmd_info():
    return redis.hget(REDIS_KEY_MENU, "cmd_info") or ""


def get_hello_image():
    return redis.hget(REDIS_KEY_MENU, "hello_image") or ""


def get_about_bot_image():
    return redis.hget(REDIS_KEY_MENU, "about_image") or ""


# ============================================================
# BOT COMMANDS
# ============================================================

def load_bot_commands_to_redis():
    sheet = get_sheet("Инфо")
    if not sheet:
        return

    headers = sheet.row_values(1)

    cmd_index = headers.index("cmd_bot") + 1
    text_index = headers.index("cmd_bot_text") + 1
    deb_cmd_index = headers.index("cmd_bot_deb") + 1
    deb_text_index = headers.index("cmd_bot_deb_text") + 1

    cmd_values = sheet.col_values(cmd_index)[1:]
    text_values = sheet.col_values(text_index)[1:]
    deb_cmd_values = sheet.col_values(deb_cmd_index)[1:]
    deb_text_values = sheet.col_values(deb_text_index)[1:]

    bot_cmd = []
    for cmd, text in zip(cmd_values, text_values):
        cmd = cmd.strip() if cmd else ""
        text = text.strip() if text else ""
        if not cmd:
            break
        bot_cmd.append(f"{cmd} — {text}" if text else cmd)

    bot_deb = []
    for cmd, text in zip(deb_cmd_values, deb_text_values):
        cmd = cmd.strip() if cmd else ""
        text = text.strip() if text else ""
        if not cmd:
            break
        bot_deb.append(f"{cmd} — {text}" if text else cmd)

    redis_replace_list(REDIS_KEY_BOT_CMD, bot_cmd)
    redis_replace_list(REDIS_KEY_BOT_DEB_CMD, bot_deb)


def get_bot_commands() -> list[str]:
    data = redis.lrange(REDIS_KEY_BOT_CMD, 0, -1)
    return data if data else ["Команды недоступны"]


def get_bot_deb_cmd() -> list[str]:
    data = redis.lrange(REDIS_KEY_BOT_DEB_CMD, 0, -1)
    return data if data else ["Команды недоступны"]
