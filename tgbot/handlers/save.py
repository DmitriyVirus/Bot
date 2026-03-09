import os
import re
import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from tgbot.sheets.gspread_client import get_gspread_client

logger = logging.getLogger(__name__)
router = Router()

# ─── Конфиг ──────────────────────────────────────────────────────────────────

SHEET_NAME = os.environ.get("SHEET_NAME")
SAVES_WORKSHEET = "Сохранения"
LINKS_WORKSHEET = "Ссылки"

FILE_TYPE_MAP = {
    "photo": "фото",
    "video": "видео",
    "animation": "гиф",
    "document": "документ",
}

URL_PATTERN = re.compile(r"https?://\S+")


# ─── FSM States ───────────────────────────────────────────────────────────────

class SaveStates(StatesGroup):
    waiting_for_name = State()


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


def add_save_record(name: str, file_type: str, file_id: str) -> bool:
    sheet = get_sheet(SAVES_WORKSHEET)
    if not sheet:
        return False
    try:
        sheet.append_row([name, file_type, file_id])
        logger.info(f"Сохранения: {name} | {file_type} | {file_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в Сохранения: {e}")
        return False


def add_link_record(name: str, url: str) -> bool:
    sheet = get_sheet(LINKS_WORKSHEET)
    if not sheet:
        return False
    try:
        sheet.append_row([name, url])
        logger.info(f"Ссылки: {name} | {url}")
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


def extract_url(text: str | None) -> str | None:
    if not text:
        return None
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None


async def delete_messages(bot, chat_id: int, *msg_ids):
    for msg_id in msg_ids:
        if msg_id:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:
                pass


# ─── Хендлеры ────────────────────────────────────────────────────────────────

@router.message(F.chat.type == "private", F.content_type.in_({"photo", "video", "animation", "document"}))
async def handle_media(message: Message, state: FSMContext):
    file_type, file_id = detect_content(message)
    if not file_type:
        return

    prompt = await message.answer("Как назвать этот файл?")
    await state.set_state(SaveStates.waiting_for_name)
    await state.update_data(
        source="telegram",
        file_type=file_type,
        file_id=file_id,
        source_msg_id=message.message_id,
        prompt_msg_id=prompt.message_id,
    )


@router.message(F.chat.type == "private", F.text, lambda m: bool(extract_url(m.text)))
async def handle_link(message: Message, state: FSMContext):
    url = extract_url(message.text)

    prompt = await message.answer("Как назвать эту ссылку?")
    await state.set_state(SaveStates.waiting_for_name)
    await state.update_data(
        source="link",
        url=url,
        source_msg_id=message.message_id,
        prompt_msg_id=prompt.message_id,
    )


@router.message(F.chat.type == "private", SaveStates.waiting_for_name, F.text)
async def handle_save_name(message: Message, state: FSMContext):
    data = await state.get_data()
    name = message.text.strip()
    source = data.get("source")
    source_msg_id = data.get("source_msg_id")
    prompt_msg_id = data.get("prompt_msg_id")

    await state.clear()

    # ── Telegram файл ─────────────────────────────────────────────────────────
    if source == "telegram":
        file_type = data.get("file_type")
        file_id = data.get("file_id")
        type_label = FILE_TYPE_MAP.get(file_type, file_type)
        success = add_save_record(name, type_label, file_id)

        if success:
            await message.answer(f'Файл "{name}" добавлен ✅')
        else:
            await message.answer("❌ Ошибка при записи в таблицу.")

    # ── Ссылка ────────────────────────────────────────────────────────────────
    elif source == "link":
        url = data.get("url")
        success = add_link_record(name, url)

        if success:
            await message.answer(f'Ссылка "{name}" добавлена ✅')
        else:
            await message.answer("❌ Ошибка при записи в таблицу.")

    await delete_messages(
        message.bot, message.chat.id,
        source_msg_id, prompt_msg_id, message.message_id
    )
