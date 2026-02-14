import re
import logging
from .gspread_client import get_gspread_client

logger = logging.getLogger(__name__)

SHEET_NAME = "DareDevils"
INFO_WORKSHEET = "Инфо"
ID_WORKSHEET = "ID"


# ===== ЧТЕНИЕ КОЛОНОК =====

def get_info_column_by_header(header_name: str) -> str:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        headers = sheet.row_values(1)
        if header_name not in headers:
            return f"Колонка '{header_name}' не найдена"
        col_index = headers.index(header_name) + 1
        values = sheet.col_values(col_index)[1:]
    except Exception as e:
        logger.error(f"Ошибка чтения колонки '{header_name}': {e}")
        return "Данные недоступны"

    return "\n".join(row for row in values if row)


def get_bot_commands() -> list[str]:
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
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
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
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


# ===== УЧАСТНИКИ ЧАТА =====

def fetch_participants() -> dict:
    """
    Загружает участников из листа ID и возвращает словарь вида:
    {alias_lower: {name, tgnick, nick, about}}
    """
    client = get_gspread_client()
    if not client:
        return {}

    try:
        sheet = client.open(SHEET_NAME).worksheet(ID_WORKSHEET)
        records = sheet.get_all_records()
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
    """
    Загружает всех админов из листа 'Админы' Google Sheets.
    Возвращает список словарей с ключами 'id' и 'name'.
    """
    client = get_gspread_client()
    if not client:
        return []

    try:
        sheet = client.open("DareDevils").worksheet("Админы")
        records = sheet.get_all_records()
        return records
    except Exception as e:
        logging.error(f"Ошибка загрузки админов: {e}")
        return []

def get_welcome() -> str:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"
    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        values = sheet.get("A2:A19")  # Диапазон A2:A19
        flat_values = [row[0] for row in values if row]
    except Exception as e:
        logger.error(f"Ошибка чтения ячеек A2:A19: {e}")
        return "Данные недоступны"
    return "".join(flat_values)  # Склеиваем в одну строку

def get_hello() -> str:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"
    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        values = sheet.get("B2:B19")  # Диапазон B2:B19
        flat_values = [row[0] for row in values if row]
    except Exception as e:
        logger.error(f"Ошибка чтения ячеек B2:B19: {e}")
        return "Данные недоступны"
    return "".join(flat_values)

def get_hello_image() -> str | None:
    client = get_gspread_client()
    if not client:
        return None

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        value = sheet.acell("B20").value
        return value.strip() if value else None
    except Exception as e:
        logger.error(f"Ошибка чтения ячейки B20: {e}")
        return None

def get_about_bot() -> str:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"
    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        values = sheet.get("C2:C19")  # Диапазон C2:C19
        flat_values = [row[0] for row in values if row]
    except Exception as e:
        logger.error(f"Ошибка чтения ячеек C2:C19: {e}")
        return "Данные недоступны"
    return "".join(flat_values)

def get_about_bot_image() -> str | None:
    client = get_gspread_client()
    if not client:
        return None

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        value = sheet.acell("C20").value
        return value.strip() if value else None
    except Exception as e:
        logger.error(f"Ошибка чтения ячейки B20: {e}")
        return None

def get_cmd_info() -> str:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"
    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        values = sheet.get("D2:D19")  # Диапазон A2:A19
        flat_values = [row[0] for row in values if row]
    except Exception as e:
        logger.error(f"Ошибка чтения ячеек D2:D19: {e}")
        return "Данные недоступны"
    return "".join(flat_values)  # Склеиваем в одну строку

def get_fu_data() -> tuple[str, str]:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны", ""

    try:
        sheet = client.open(SHEET_NAME).worksheet("Инфо")

        caption = sheet.acell("I2").value or ""
        media_url = sheet.acell("I3").value or ""

        return caption, media_url

    except Exception as e:
        logger.error(f"Ошибка чтения I2/I3: {e}")
        return "Данные недоступны", ""

def convert_drive_url(url: str) -> str:
    """
    Преобразует Google Drive ссылку вида:
    https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    в прямую ссылку для скачивания:
    https://drive.google.com/uc?export=download&id=FILE_ID
    """
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url  # если не Google Drive, возвращаем как есть


def get_nakol_data() -> tuple[str, str]:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны", ""

    try:
        sheet = client.open(SHEET_NAME).worksheet("Инфо")
        caption = sheet.acell("I5").value or ""
        media_url = sheet.acell("I6").value or ""

        # Преобразуем Drive-ссылку, если нужно
        media_url = convert_drive_url(media_url)

        return caption, media_url

    except Exception as e:
        logger.error(f"Ошибка чтения I2/I3: {e}")
        return "Данные недоступны", ""

def get_klaar_data() -> tuple[str, str]:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны", ""

    try:
        sheet = client.open(SHEET_NAME).worksheet("Инфо")
        caption = sheet.acell("I8").value or ""
        media_url = sheet.acell("I9").value or ""

        # Преобразуем Drive-ссылку, если нужно
        media_url = convert_drive_url(media_url)

        return caption, media_url

    except Exception as e:
        logger.error(f"Ошибка чтения I2/I3: {e}")
        return "Данные недоступны", ""

