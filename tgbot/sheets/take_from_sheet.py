import os
import logging
from .gspread_client import get_gspread_client

logger = logging.getLogger(__name__)

SHEET_NAME = os.environ.get("SHEET_NAME")
ID_WORKSHEET = "ID"


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


# ===== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ =====
def is_user_exists(user_id: int) -> bool:
    """
    Проверяет, есть ли пользователь в листе ID.
    """
    sheet = get_sheet(ID_WORKSHEET)
    if not sheet:
        return False
    try:
        records = sheet.get_all_records()
        for record in records:
            if record.get("user_id") == user_id:
                return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке существования пользователя {user_id}: {e}")
        return False


def add_user_to_sheet_safe(user_id: int, username: str, first_name: str, last_name: str):
    """
    Добавляет пользователя в лист ID, если его нет.
    Используется для блокирующего вызова в отдельном потоке.
    """
    sheet = get_sheet(ID_WORKSHEET)
    if not sheet:
        logger.error("Не удалось получить лист ID для добавления пользователя")
        return
    try:
        if is_user_exists(user_id):
            logger.info(f"Пользователь {user_id} уже существует в листе ID")
            return

        # Добавляем нового пользователя с дефолтными значениями
        sheet.append_row([
            user_id,
            username,
            first_name,
            last_name,
            "выясняем",  # name
            "выясняем",  # aliases
            "выясняем"   # about
        ])
        logger.info(f"Пользователь {username} ({user_id}) успешно добавлен в лист ID")
    except Exception as e:
        logger.error(f"Ошибка при добавлении пользователя {user_id}: {e}")
