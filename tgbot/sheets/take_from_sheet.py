import logging
from .gspread_client import get_gspread_client

logger = logging.getLogger(__name__)


def get_info_column_by_header(header_name: str) -> str:
    """
    Читает колонку по имени заголовка (header_name) в листе 'Инфо'
    и возвращает текст, склеенный через перенос строки.
    """
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
        headers = sheet.row_values(1)
        if header_name not in headers:
            return f"Колонка '{header_name}' не найдена"
        col_index = headers.index(header_name) + 1
        values = sheet.col_values(col_index)[1:]  # пропускаем заголовок
    except Exception as e:
        logger.error(f"Ошибка чтения колонки '{header_name}': {e}")
        return "Данные недоступны"

    return "\n".join(row for row in values if row)


def get_bot_commands() -> list[str]:
    """
    Читает основные команды бота (cmd_bot + cmd_bot_text)
    """
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
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
    """
    Читает команды отладки бота (cmd_bot_deb + cmd_bot_deb_text)
    """
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
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
