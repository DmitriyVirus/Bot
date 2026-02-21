import os
import io
import logging
from PIL import Image
import httpx
from aiogram import Bot, Router, F, types

# ---------- Настройки ----------
OCR_API_KEY = os.getenv("OCR_API_KEY")  # Берем ключ из переменной окружения
if not OCR_API_KEY:
    raise RuntimeError("OCR_API_KEY не задан в переменных окружения")
OCR_URL = "https://api.ocr.space/parse/image"

router = Router()

# ---------- OCR функция ----------
async def extract_text_from_telegram_photo(bot: Bot, file_id: str, max_mb=1) -> str:
    """
    Получает file_id фото из Telegram, сжимает/увеличивает изображение при необходимости
    и возвращает распознанный текст через OCR.Space
    """
    # 1. Получаем файл из Telegram
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    image_bytes = file_bytes.read()

    # 2. Проверяем размер файла
    size_mb = len(image_bytes) / (1024 * 1024)
    image = Image.open(io.BytesIO(image_bytes))

    # Увеличиваем маленькие картинки для лучшего OCR
    if image.width < 500:
        factor = 2
        image = image.resize((image.width * factor, image.height * factor))

    # Сжимаем, если больше max_mb
    output = io.BytesIO()
    if size_mb > max_mb:
        image.thumbnail((1024, 1024))  # максимальный размер 1024x1024
        image.save(output, format="JPEG", quality=70)
    else:
        image.save(output, format="JPEG", quality=90)
    image_bytes = output.getvalue()

    # 3. Отправляем в OCR.Space
    files = {"file": ("image.jpg", image_bytes)}
    data = {
        "apikey": OCR_API_KEY,
        "language": "rus,eng",
        "isOverlayRequired": False
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(OCR_URL, files=files, data=data)
        result = response.json()
    except Exception as e:
        logging.error(f"OCR request failed: {e}")
        return "❌ Ошибка запроса к OCR"

    # 4. Получаем текст
    try:
        parsed = result.get("ParsedResults")
        if not parsed:
            return "❌ OCR вернул пустой результат"
        text = parsed[0].get("ParsedText", "")
        if not text.strip():
            return "❌ Текст не найден"
        return text.strip()
    except Exception as e:
        logging.error(f"OCR parsing failed: {e}")
        return "❌ Ошибка обработки OCR ответа"


# ---------- Хэндлеры ----------
async def handle_photo_message(message: types.Message):
    if not message.photo:
        return
    photo = message.photo[-1]  # самая большая версия
    text = await extract_text_from_telegram_photo(message.bot, photo.file_id)
    await message.answer(f"📄 Распознанный текст:\n{text}")


async def handle_photo_channel_post(message: types.Message):
    if not message.photo:
        return
    photo = message.photo[-1]
    text = await extract_text_from_telegram_photo(message.bot, photo.file_id)
    await message.bot.send_message(chat_id=message.chat.id, text=f"📄 Распознанный текст:\n{text}")


# ---------- Роутеры ----------
router.message(F.photo)(handle_photo_message)
router.channel_post(F.photo)(handle_photo_channel_post)
