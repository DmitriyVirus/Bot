import re
import logging
from .gspread_client import get_gspread_client

logger = logging.getLogger(__name__)

SHEET_NAME = "DareDevils"
INFO_WORKSHEET = "Инфо"
ID_WORKSHEET = "ID"
ADMINS_WORKSHEET = "Админы"


# ===== ВСПОМОГАТЕЛЬНЫЕ =====

def get_sheet(name: str):
    client = get_gspread_client()
    if not client:
        return None
    try:
        return client.open(SHEET_NAME).worksheet(name)
    except Exception as e:
        logger.error(f"Ошибка открытия листа {name}: {e}")
        return None


def get_range_text(range_name: str) -> str:
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return "Данные недоступны"

    try:
        values = sheet.get(range_name)
        flat = [row[0] for row in values if row]
        return "\n".join(flat)
    except Exception as e:
        logger.error(f"Ошибка чтения диапазона {range_name}: {e}")
        return "Данные недоступны"


def get_cell_value(cell: str) -> str | None:
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return None
    try:
        value = sheet.acell(cell).value
        return value.strip() if value else None
    except Exception as e:
        logger.error(f"Ошибка чтения ячейки {cell}: {e}")
        return None


def get_media_block(caption_cell: str, media_cell: str) -> tuple[str, str]:
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return "Данные недоступны", ""

    try:
        caption = sheet.acell(caption_cell).value or ""
        media_url = sheet.acell(media_cell).value or ""
        media_url = convert_drive_url(media_url)
        return caption, media_url
    except Exception as e:
        logger.error(f"Ошибка чтения {caption_cell}/{media_cell}: {e}")
        return "Данные недоступны", ""


# ===== GOOGLE DRIVE =====

def convert_drive_url(url: str) -> str:
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


# ===== ТЕКСТЫ =====

def get_welcome() -> str:
    return get_range_text("A2:A19")


def get_hello() -> str:
    return get_range_text("B2:B19")


def get_about_bot() -> str:
    return get_range_text("C2:C19")


def get_cmd_info() -> str:
    return get_range_text("D2:D19")


def get_hello_image() -> str | None:
    return get_cell_value("B20")


def get_about_bot_image() -> str | None:
    return get_cell_value("C20")


# ===== MEDIA КОМАНДЫ =====

def get_fu_data() -> tuple[str, str]:
    return get_media_block("I2", "I3")


def get_nakol_data() -> tuple[str, str]:
    return get_media_block("I5", "I6")


def get_klaar_data() -> tuple[str, str]:
    return get_media_block("I8", "I9")


def get_kris_data() -> tuple[str, str]:
    return get_media_block("I11", "I12")


# ===== АДМИНЫ =====

def get_admins_records() -> list[dict]:
    sheet = get_sheet(ADMINS_WORKSHEET)
    if not sheet:
        return []
    try:
        return sheet.get_all_records()
    except Exception as e:
        logger.error(f"Ошибка загрузки админов: {e}")
        return []
