import os
import re
import logging
from .gspread_client import get_gspread_client

logger = logging.getLogger(__name__)

SHEET_NAME = os.environ.get("SHEET_NAME")
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


# ===== ВОЗВРАЩАЕМЫЕ ФУНКЦИИ =====

def get_info_column_by_header(header_name: str) -> str:
    """
    Возвращает все значения колонки по её заголовку.
    """
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return "Данные недоступны"
    try:
        headers = sheet.row_values(1)
        if header_name not in headers:
            return f"Колонка '{header_name}' не найдена"
        col_index = headers.index(header_name) + 1
        values = sheet.col_values(col_index)[1:]
        return "\n".join(row for row in values if row)
    except Exception as e:
        logger.error(f"Ошибка чтения колонки '{header_name}': {e}")
        return "Данные недоступны"


def get_bot_commands() -> list[str]:
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return ["Команды недоступны"]
    try:
        headers = sheet.row_values(1)
        c_index = headers.index("cmd_bot") + 1
        d_index = headers.index("cmd_bot_text") + 1
        cmd_values = sheet.col_values(c_index)[1:]
        text_values = sheet.col_values(d_index)[1:]
    except Exception as e:
        logger.error(f"Ошибка чтения команд бота: {e}")
        return ["Команды недоступны"]

    commands = []
    for cmd, text in zip(cmd_values, text_values):
        cmd = cmd.strip() if cmd else ""
        text = text.strip() if text else ""
        if not cmd:
            continue
        commands.append(f"{cmd} — {text}" if text else cmd)
    return commands


def get_bot_deb_cmd() -> list[str]:
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return ["Команды недоступны"]
    try:
        headers = sheet.row_values(1)
        c_index = headers.index("cmd_bot_deb") + 1
        d_index = headers.index("cmd_bot_deb_text") + 1
        cmd_values = sheet.col_values(c_index)[1:]
        text_values = sheet.col_values(d_index)[1:]
    except Exception as e:
        logger.error(f"Ошибка чтения debug-команд: {e}")
        return ["Команды недоступны"]

    commands = []
    for cmd, text in zip(cmd_values, text_values):
        cmd = cmd.strip() if cmd else ""
        text = text.strip() if text else ""
        if not cmd:
            continue
        commands.append(f"{cmd} — {text}" if text else cmd)
    return commands


# ===== УЧАСТНИКИ =====

def fetch_participants() -> dict:
    client = get_sheet(ID_WORKSHEET)
    if not client:
        return {}
    try:
        records = client.get_all_records()
        expanded_table = {}
        for record in records:
            first_name = record["first_name"]
            last_name = record["last_name"]
            if first_name.lower() == "unknown" and last_name.lower() == "unknown":
                tgnick = "Unknown"
            elif first_name.lower() == "unknown":
                tgnick = last_name.strip()
            elif last_name.lower() == "unknown":
                tgnick = first_name.strip()
            else:
                tgnick = f"{first_name} {last_name}".strip()
            user_data = {
                "name": record["name"],
                "tgnick": tgnick,
                "nick": record["username"],
                "about": record["about"]
            }
            expanded_table[record["name"].lower()] = user_data
            if record["aliases"]:
                aliases = [alias.strip().lower() for alias in record["aliases"].split(",")]
                for alias in aliases:
                    expanded_table[alias] = user_data
        return expanded_table
    except Exception as e:
        logger.error(f"Ошибка загрузки участников из Google Sheets: {e}")
        return {}


def get_admins_records() -> list[dict]:
    sheet = get_sheet(ADMINS_WORKSHEET)
    if not sheet:
        return []
    try:
        return sheet.get_all_records()
    except Exception as e:
        logger.error(f"Ошибка загрузки админов: {e}")
        return []


def get_user_from_sheet(user_id: int):
    sheet = get_sheet(ID_WORKSHEET)  # Раньше client.open("DareDevils").worksheet("ID")
    if not sheet:
        return None
    try:
        data = sheet.get_all_records()
        for row in data:
            if row.get('user_id') == user_id:
                return row.get('name')
    except Exception as e:
        logger.error(f"Ошибка при get_user_from_sheet(): {e}")
    return None


# ==========================
# Получение списка разрешенных ID пользователей
# ==========================
def get_allowed_user_ids():
    sheet = get_sheet("Добавление")  # Раньше client.open("DareDevils").worksheet("Добавление")
    if not sheet:
        return set()
    try:
        data = sheet.get_all_records()
        return set(int(row["id"]) for row in data if "id" in row and row["id"])
    except Exception as e:
        logger.error(f"Ошибка при get_allowed_user_ids(): {e}")
        return set()


# ==========================
# Получение данных из колонки листа "Автосбор"
# ==========================
def get_column_data_from_autosbor(column_index: int):
    """
    Возвращает список значений из колонки column_index листа "Автосбор".
    column_index: 1 = первый столбец
    """
    sheet = get_sheet("Автосбор")  # Раньше client.open("DareDevils").worksheet("Автосбор")
    if not sheet:
        return []
    try:
        all_values = sheet.get_all_values()
        if not all_values or column_index <= 0 or column_index > len(all_values[0]):
            return []
        col_data = [row[column_index - 1].strip() for row in all_values if row[column_index - 1].strip()]
        return col_data
    except Exception as e:
        logger.error(f"Ошибка при get_column_data_from_autosbor(): {e}")
        return []


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

# ===== ТЕКСТ И КАРТИНКА ДЛЯ СОБЫТИЙ =====

def get_bal_data() -> tuple[str, str]:
    """Текст и картинка для /bal"""
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return "Данные недоступны", ""
    try:
        text = sheet.acell("A2").value or ""
        media_url = sheet.acell("B2").value or ""
        media_url = convert_drive_url(media_url)
        return text, media_url
    except Exception as e:
        logger.error(f"Ошибка при get_bal_data(): {e}")
        return "Данные недоступны", ""

def get_inn_data() -> tuple[str, str]:
    """Текст и картинка для /inn"""
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return "Данные недоступны", ""
    try:
        text = sheet.acell("A3").value or ""
        media_url = sheet.acell("B3").value or ""
        media_url = convert_drive_url(media_url)
        return text, media_url
    except Exception as e:
        logger.error(f"Ошибка при get_inn_data(): {e}")
        return "Данные недоступны", ""

def get_ork_data() -> tuple[str, str]:
    """Текст и картинка для /ork"""
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return "Данные недоступны", ""
    try:
        text = sheet.acell("A4").value or ""
        media_url = sheet.acell("B4").value or ""
        media_url = convert_drive_url(media_url)
        return text, media_url
    except Exception as e:
        logger.error(f"Ошибка при get_ork_data(): {e}")
        return "Данные недоступны", ""

def get_inst_data() -> tuple[str, str]:
    """Текст и картинка для /inst"""
    sheet = get_sheet(INFO_WORKSHEET)
    if not sheet:
        return "Данные недоступны", ""
    try:
        text = sheet.acell("A5").value or ""
        media_url = sheet.acell("B5").value or ""
        media_url = convert_drive_url(media_url)
        return text, media_url
    except Exception as e:
        logger.error(f"Ошибка при get_inst_data(): {e}")
        return "Данные недоступны", ""
