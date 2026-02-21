import io
import logging
import os
from PIL import Image, ImageEnhance, ImageOps
import httpx
from aiogram import types, Router, F

OCR_API_KEY = os.getenv("OCR_API_KEY")
OCR_URL = "https://api.ocr.space/parse/image"

router = Router()


async def extract_text_from_telegram_photo(bot, file_id: str) -> str:
    try:
        # 1. Получаем файл из Telegram
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        image_bytes = file_bytes.read()

        # 2. Открываем изображение
        image = Image.open(io.BytesIO(image_bytes))

        # 3. Улучшаем качество для OCR
        image = image.convert("L")  # grayscale

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)

        image = ImageOps.autocontrast(image)

        # увеличение маленьких изображений
        if image.width < 1000:
            factor = 2
            image = image.resize(
                (image.width * factor, image.height * factor)
            )

        # 4. Сохраняем в память
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=95)
        image_bytes = output.getvalue()

        # 5. Отправляем в OCR.Space
        files = {"file": ("image.jpg", image_bytes)}
        data = {
            "apikey": OCR_API_KEY,
            "language": "eng,rus",
            "isOverlayRequired": False,
            "OCREngine": 2  # более точный движок
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(OCR_URL, files=files, data=data)

        result = response.json()

        parsed = result.get("ParsedResults")
        if not parsed:
            return "❌ OCR вернул пустой результат"

        text = parsed[0].get("ParsedText", "").strip()

        return text if text else "❌ Текст не найден"

    except Exception as e:
        logging.exception(f"OCR failed: {e}")
        return "❌ Ошибка обработки OCR"


# ---------- Хендлер ----------
@router.message(F.photo, F.chat.type == "private")
async def handle_private_photo(message: types.Message):
    photo = message.photo[-1]
    bot = message.bot

    text = await extract_text_from_telegram_photo(bot, photo.file_id)

    await message.answer(f"📄 Распознанный текст:\n\n{text}")
