import os
import re
import logging
import aiohttp
import aiofiles

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sheets.gspread_client import get_gspread_client  # ← поправь путь если нужно

logger = logging.getLogger(__name__)
router = Router()

# ─── Конфиг ──────────────────────────────────────────────────────────────────

SHEET_NAME = os.environ.get("SHEET_NAME")
SAVES_WORKSHEET = "Сохранения"
COBALT_API = "https://api.cobalt.tools/api/json"
TEMP_DIR = "/tmp/yt_downloads"

os.makedirs(TEMP_DIR, exist_ok=True)

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


# ─── YouTube (cobalt.tools) ───────────────────────────────────────────────────

async def download_youtube_video(url: str, filename: str) -> str | None:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "vQuality": "720",
        "filenamePattern": "basic",
        "isNoTTWatermark": True,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(COBALT_API, json=payload, headers=headers) as resp:
            if resp.status != 200:
                logger.error(f"Cobalt API статус: {resp.status}")
                return None

            data = await resp.json()
            status = data.get("status")

            if status == "error":
                logger.error(f"Cobalt ошибка: {data.get('text')}")
                return None

            if status not in ("stream", "redirect", "tunnel"):
                logger.error(f"Cobalt неожиданный статус: {status}")
                return None

            download_url = data.get("url")
            if not download_url:
                logger.error("Cobalt не вернул url")
                return None

        file_path = os.path.join(TEMP_DIR, f"{filename}.mp4")
        async with session.get(download_url) as file_resp:
            if file_resp.status != 200:
                logger.error(f"Ошибка скачивания: {file_resp.status}")
                return None

            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in file_resp.content.iter_chunked(1024 * 64):
                    await f.write(chunk)

    return file_path


def cleanup_file(file_path: str):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Ошибка удаления файла: {e}")


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

@router.message(F.content_type.in_({"photo", "video", "animation", "document"}))
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


@router.message(F.text.regexp(YOUTUBE_PATTERN))
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


@router.message(SaveStates.waiting_for_name, F.text)
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
        processing_msg = await message.answer("⏳ Скачиваю видео, подождите...")

        file_path = await download_youtube_video(youtube_url, name)

        if not file_path:
            await processing_msg.edit_text("❌ Не удалось скачать видео.")
            return

        try:
            with open(file_path, "rb") as video_file:
                sent = await message.bot.send_video(
                    chat_id=message.chat.id,
                    video=video_file,
                )

            tg_file_id = sent.video.file_id
            type_label = FILE_TYPE_MAP.get("youtube", "youtube видео")
            success = add_save_record(name, type_label, tg_file_id)

            if success:
                await message.answer(f'Файл "{name}" добавлен ✅')
            else:
                await message.answer("❌ Видео загружено, но ошибка при записи в таблицу.")

        finally:
            cleanup_file(file_path)

        await delete_messages(
            message.bot, message.chat.id,
            source_msg_id, prompt_msg_id, message.message_id, processing_msg.message_id
        )
