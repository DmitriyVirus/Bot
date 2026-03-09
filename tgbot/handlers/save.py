import os
import re
import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from tgbot.sheets.gspread_client import get_gspread_client

logger = logging.getLogger(__name__)
router = Router()

# ─── Конфиг ──────────────────────────────────────────────────────────────────

SHEET_NAME = os.environ.get("SHEET_NAME")
SAVES_WORKSHEET = "Сохранения"
LINKS_WORKSHEET = "Ссылки"
DEFAULT_NAME = "Забавно"

FILE_TYPE_MAP = {
    "photo": "фото",
    "video": "видео",
    "animation": "гиф",
    "document": "документ",
}

URL_PATTERN = re.compile(r"https?://\S+")


# ─── Google Sheets ────────────────────────────────────────────────────────────

def get_sheet(worksheet_name: str):
    client = get_gspread_client()
    if not client:
        return None
    try:
        return client.open(SHEET_NAME).worksheet(worksheet_name)
    except Exception as e:
        logger.error(f"Ошибка открытия листа '{worksheet_name}': {e}")
        return None


def add_save_record(file_type: str, file_id: str) -> bool:
    sheet = get_sheet(SAVES_WORKSHEET)
    if not sheet:
        return False
    try:
        sheet.append_row([DEFAULT_NAME, file_type, file_id])
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в Сохранения: {e}")
        return False


def add_link_record(url: str) -> bool:
    sheet = get_sheet(LINKS_WORKSHEET)
    if not sheet:
        return False
    try:
        sheet.append_row([DEFAULT_NAME, url])
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в Ссылки: {e}")
        return False


# ─── Вспомогательные ─────────────────────────────────────────────────────────

def detect_content(message: Message) -> tuple[str, str] | tuple[None, None]:
    if message.photo:
        return "photo", message.photo[-1].file_id
    if message.video:
        return "video", message.video.file_id
    if message.animation:
        return "animation", message.animation.file_id
    if message.document:
        return "document", message.document.file_id
    return None, None


async def delete_and_notify(message: Message):
    try:
        await message.delete()
    except Exception:
        pass
    msg = await message.answer("сохранено")
    # удаляем уведомление через 3 секунды
    import asyncio
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


# ─── Хендлеры ────────────────────────────────────────────────────────────────

@router.message(F.chat.type == "private", F.content_type.in_({"photo", "video", "animation", "document"}))
async def handle_media(message: Message, state: FSMContext):
    file_type, file_id = detect_content(message)
    if not file_type:
        return

    type_label = FILE_TYPE_MAP.get(file_type, file_type)
    add_save_record(type_label, file_id)
    await delete_and_notify(message)


@router.message(F.chat.type == "private", F.text, lambda m: bool(URL_PATTERN.search(m.text or "")))
async def handle_link(message: Message, state: FSMContext):
    match = URL_PATTERN.search(message.text)
    url = match.group(0)
    add_link_record(url)
    await delete_and_notify(message)
