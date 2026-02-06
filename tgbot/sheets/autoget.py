import logging
from aiogram import Router
from aiogram.types import Message
from tgbot.gspread_client import get_gspread_client

router = Router()
logging.basicConfig(level=logging.INFO)

SHEET_NAME = "DareDevils"
WORKSHEET_NAME = "ID"


def get_sheet():
    client = get_gspread_client()
    if not client:
        return None
    return client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)


def is_user_exists(sheet, user_id: int) -> bool:
    try:
        records = sheet.get_all_values()[1:]  # пропускаем заголовок
        return any(str(user_id) == row[0] for row in records)
    except Exception as e:
        logging.error(f"is_user_exists error: {e}")
        return False


def add_user_to_sheet(user_id, username, first_name, last_name):
    sheet = get_sheet()
    if not sheet:
        return

    if is_user_exists(sheet, user_id):
        return

    try:
        sheet.append_row([
            user_id,
            username or "",
            first_name or "",
            last_name or "",
            "выясняем",
            "выясняем",
            "выясняем"
        ])
        logging.info(f"User {user_id} added to sheet")
    except Exception as e:
        logging.error(f"add_user_to_sheet error: {e}")


@router.message()
async def autoget_user(message: Message):
    user = message.from_user
    if not user:
        return

    add_user_to_sheet(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
