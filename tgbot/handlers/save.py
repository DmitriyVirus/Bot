import os
import re
import logging
import aiohttp

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
YTDLP_API = "https://web-production-8cf1f3.up.railway.app"

YOUTUBE_PATTERN = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+"
)

FILE_TYPE_MAP = {
    "photo": "фото",
    "video": "видео",
    "animation": "гиф",
    "document": "документ",
    "youtube": "youtube видео",
}


# ─── FSM States ───────────────────────────────────────────────────────────────

class SaveStates(StatesGroup):
    waiting_for_name = State()


# ─── Google Sheets ────────────────────────────────────────────────────────────

def get_saves_sheet():
    client = get_gspread_client()
    if not client:
        return None
    try:
        return client.open(SHEET_NAME).worksheet(SAVES_WORKSHEET)
    except Exception as e:
        logger.error(f"Ошибка открытия листа '{SAVES_WORKSHEET}': {e}")
        return None


def add_save_record(name: str, file_type: str, file_id: str) -> bool:
    sheet = get_saves_sheet()
    if not sheet:
        return False
    try:
        sheet.append_row([name, file_type, file_id])
        logger.info(f"Запись добавлена: {name} | {file_type} | {file_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в таблицу: {e}")
        return False


# ─── YouTube (yt-dlp на Railway) ─────────────────────────────────────────────

async def get_youtube_direct_url(url: str) -> str | None:
    """
    Получает прямую ссылку на видео через yt-dlp сервис на Railway.
    Telegram сам скачает видео по этой ссылке.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{YTDLP_API}/get_url",
            params={"url": url, "quality": "720"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"yt-dlp сервис статус: {resp.status}, тело: {text}")
                return None

            data = await resp.json()
            if data.get("status") != "ok":
                logger.error(f"yt-dlp ошибка: {data.get('error')}")
                return None

            return data.get("url")


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


def is_youtube_link(text: str | None) -> bool:
    if not text:
        return False
    return bool(YOUTUBE_PATTERN.search(text))


def extract_youtube_url(text: str) -> str | None:
    match = YOUTUBE_PATTERN.search(text)
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


@router.message(F.chat.type == "private", F.text.regexp(YOUTUBE_PATTERN))
async def handle_youtube_link(message: Message, state: FSMContext):
    url = extract_youtube_url(message.text)
    if not url:
        return

    prompt = await message.answer("Как назвать это видео?")
    await state.set_state(SaveStates.waiting_for_name)
    await state.update_data(
        source="youtube",
        file_type="youtube",
        youtube_url=url,
        source_msg_id=message.message_id,
        prompt_msg_id=prompt.message_id,
    )


@router.message(F.chat.type == "private", SaveStates.waiting_for_name, F.text)
async def handle_save_name(message: Message, state: FSMContext):
    data = await state.get_data()
    name = message.text.strip()
    source = data.get("source")
    file_type = data.get("file_type")
    source_msg_id = data.get("source_msg_id")
    prompt_msg_id = data.get("prompt_msg_id")

    await state.clear()

    # ── Telegram файл ─────────────────────────────────────────────────────────
    if source == "telegram":
        file_id = data.get("file_id")
        type_label = FILE_TYPE_MAP.get(file_type, file_type)
        success = add_save_record(name, type_label, file_id)

        if success:
            await message.answer(f'Файл "{name}" добавлен ✅')
        else:
            await message.answer("❌ Ошибка при записи в таблицу.")

        await delete_messages(
            message.bot, message.chat.id,
            source_msg_id, prompt_msg_id, message.message_id
        )

    # ── YouTube ───────────────────────────────────────────────────────────────
    elif source == "youtube":
        youtube_url = data.get("youtube_url")
        processing_msg = await message.answer("⏳ Получаю ссылку на видео...")

        direct_url = await get_youtube_direct_url(youtube_url)

        if not direct_url:
            await processing_msg.edit_text("❌ Не удалось получить ссылку на видео.")
            return

        # Telegram сам скачивает видео по прямой ссылке — Vercel не участвует
        sent = await message.bot.send_video(
            chat_id=message.chat.id,
            video=direct_url,
        )

        tg_file_id = sent.video.file_id
        type_label = FILE_TYPE_MAP.get("youtube", "youtube видео")
        success = add_save_record(name, type_label, tg_file_id)

        if success:
            await message.answer(f'Файл "{name}" добавлен ✅')
        else:
            await message.answer("❌ Видео загружено, но ошибка при записи в таблицу.")

        await delete_messages(
            message.bot, message.chat.id,
            source_msg_id, prompt_msg_id, message.message_id, processing_msg.message_id
        )
