import io
import logging
import os
import re
from PIL import Image, ImageEnhance, ImageOps
import httpx
from aiogram import types, Router, F

OCR_API_KEY = os.getenv("OCR_API_KEY")
OCR_URL = "https://api.ocr.space/parse/image"

router = Router()


async def extract_game_data_from_photo(bot, file_id: str):
    try:
        # 1. Получаем файл из Telegram
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        image_bytes = file_bytes.read()

        image = Image.open(io.BytesIO(image_bytes))

        # -------------------------------------------------
        # 2. Вырезаем верхнюю часть (где имя)
        # -------------------------------------------------
        width, height = image.size
        top_crop = image.crop((0, 0, width, int(height * 0.20)))

        # -------------------------------------------------
        # 3. Усиливаем белый текст
        # -------------------------------------------------
        top_crop = top_crop.convert("L")  # grayscale
        enhancer = ImageEnhance.Contrast(top_crop)
        top_crop = enhancer.enhance(2.5)

        # немного "выбелим"
        top_crop = ImageOps.autocontrast(top_crop)

        # увеличение мелкого текста
        if top_crop.width < 800:
            factor = 2
            top_crop = top_crop.resize(
                (top_crop.width * factor, top_crop.height * factor)
            )

        # -------------------------------------------------
        # 4. Отправляем в OCR
        # -------------------------------------------------
        output = io.BytesIO()
        top_crop.save(output, format="JPEG", quality=95)
        image_bytes = output.getvalue()

        files = {"file": ("image.jpg", image_bytes)}
        data = {
            "apikey": OCR_API_KEY,
            "language": "eng",
            "isOverlayRequired": False
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(OCR_URL, files=files, data=data)

        result = response.json()

        parsed = result.get("ParsedResults")
        if not parsed:
            return None, None, None

        text = parsed[0].get("ParsedText", "").strip()

        # -------------------------------------------------
        # 5. Парсим имя
        # -------------------------------------------------
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        name = lines[0] if lines else None

        # -------------------------------------------------
        # 6. Парсим PvP / PC и число/число
        # -------------------------------------------------
        match = re.search(r"(P[vV]P|P[Cc])\s*(\d+\s*/\s*\d+)", text)

        if match:
            mode = match.group(1)
            value = match.group(2).replace(" ", "")
        else:
            mode = None
            value = None

        return name, mode, value

    except Exception as e:
        logging.exception(f"OCR failed: {e}")
        return None, None, None


# ---------- Хендлер ----------
@router.message(F.photo, F.chat.type == "private")
async def handle_private_photo(message: types.Message):
    photo = message.photo[-1]
    bot = message.bot

    name, mode, value = await extract_game_data_from_photo(
        bot, photo.file_id
    )

    if not name:
        await message.answer("❌ Не удалось распознать данные")
        return

    await message.answer(
        f"👤 Имя: {name}\n"
        f"🎮 Режим: {mode}\n"
        f"📊 Значение: {value}"
    )
