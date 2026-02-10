import logging
from .gspread_client import get_gspread_client

logger = logging.getLogger(__name__)

SHEET_NAME = "DareDevils"
INFO_WORKSHEET = "Инфо"
ID_WORKSHEET = "ID"



def get_welcome_text() -> str:
    """
    Возвращает текст приветствия из диапазона A2:A19 колонки 'Welcome'.
    """
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open(SHEET_NAME).worksheet(INFO_WORKSHEET)
        # Диапазон A2:A19
        values = sheet.get("A2:A19")
        # get() возвращает список списков, превращаем в список строк
        values = [row[0] for row in values if row and row[0].strip()]
        return "\n".join(values)
    except Exception as e:
        logger.error(f"Ошибка чтения Welcome A2:A19: {e}")
        return "Данные недоступны"



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

def get_image_from_cell(cell="B20") -> str | None:
    """
    Возвращает ссылку на изображение из конкретной ячейки (по умолчанию B30).
    """
    client = get_gspread_client()
    if not client:
        return None

    try:
        sheet = client.open(SHEET_NAME).worksheet(ID_WORKSHEET)
        value = sheet.acell(cell).value
        return value if value else None
    except Exception as e:
        logger.error(f"Ошибка чтения ячейки '{cell}': {e}")
        return None


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


