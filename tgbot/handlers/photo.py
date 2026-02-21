import io
import logging
import os
from PIL import Image, ImageEnhance
import httpx
from aiogram import types, Router, F

OCR_API_KEY = os.getenv("OCR_API_KEY")  # ключ из переменных окружения
OCR_URL = "https://api.ocr.space/parse/image"

router = Router()

async def extract_text_from_telegram_photo(bot, file_id: str, max_mb=1) -> str:
    try:
        # 1. Получаем файл
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        image_bytes = file_bytes.read()

        # 2. Открываем изображение
        image = Image.open(io.BytesIO(image_bytes))

        # 3. Ч/б
        image = image.convert("L")

        # 4. Контраст
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # 5. Увеличение мелкого текста
        if image.width < 500:
            factor = 2
            image = image.resize((image.width * factor, image.height * factor))

        # 6. Сохраняем в BytesIO
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=90)
        image_bytes = output.getvalue()

        # 7. Отправляем в OCR.Space
        files = {"file": ("image.jpg", image_bytes)}
        data = {
            "apikey": OCR_API_KEY,
            "language": "rus,eng",
            "isOverlayRequired": False
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(OCR_URL, files=files, data=data)

        result = response.json()

        # 8. Получаем текст
        parsed = result.get("ParsedResults")
        if not parsed:
            return "❌ OCR вернул пустой результат"
        text = parsed[0].get("ParsedText", "")
        return text.strip() or "❌ Текст не найден"

    except Exception as e:
        logging.exception(f"OCR failed: {e}")
        return "❌ Ошибка обработки OCR"


# ---------- Хендлер для личных сообщений ----------
@router.message(F.photo, F.chat.type == "private")
async def handle_private_photo(message: types.Message):
    photo = message.photo[-1]  # самая большая версия
    bot = message.bot  # используем bot из Message
    text = await extract_text_from_telegram_photo(bot, photo.file_id)
    await message.answer(f"📄 Распознанный текст:\n{text}")
