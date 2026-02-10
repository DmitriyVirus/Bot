import logging
from .gspread_client import get_gspread_client

logger = logging.getLogger(__name__)

SHEET_NAME = "DareDevils"
INFO_WORKSHEET = "Инфо"
ID_WORKSHEET = "ID"


# ===== ПРИВЕТСТВИЕ =====
def get_welcome_text() -> str:
    """
    Возвращает текст приветствия из диапазона A2:A19.
    """
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        values = sheet.get("A2:A19")
        values = [row[0] for row in values if row and row[0].strip()]
        return "\n".join(values)
    except Exception as e:
        logger.error(f"Ошибка чтения Welcome A2:A19: {e}")
        return "Данные недоступны"


def get_hello_text() -> str:
    """
    Возвращает текст из диапазона Hello B2:B19.
    """
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        values = sheet.get("B2:B19")
        values = [row[0] for row in values if row and row[0].strip()]
        return "\n".join(values)
    except Exception as e:
        logger.error(f"Ошибка чтения Hello B2:B19: {e}")
        return "Данные недоступны"


def get_about_bot_text() -> str:
    """
    Возвращает текст из диапазона about_bot C2:C19.
    """
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        values = sheet.get("C2:C19")
        values = [row[0] for row in values if row and row[0].strip()]
        return "\n".join(values)
    except Exception as e:
        logger.error(f"Ошибка чтения about_bot C2:C19: {e}")
        return "Данные недоступны"


# ===== ССЫЛКА НА КАРТИНКУ =====
def get_image_from_cell(cell="B20") -> str | None:
    """
    Возвращает ссылку на изображение из конкретной ячейки (по умолчанию B20).
    """
    client = get_gspread_client()
    if not client:
        return None

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        value = sheet.acell(cell).value
        return value if value else None
    except Exception as e:
        logger.error(f"Ошибка чтения ячейки '{cell}': {e}")
        return None


# ===== ЧТЕНИЕ КОМАНД =====
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


# ===== АДМИНЫ =====
def get_admins_records() -> list[dict]:
    client = get_gspread_client()
    if not client:
        return []

    try:
        sheet = client.open(SHEET_NAME).worksheet("Админы")
        records = sheet.get_all_records()
        return records
    except Exception as e:
        logging.error(f"Ошибка загрузки админов: {e}")
        return []
