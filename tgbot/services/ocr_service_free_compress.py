import io
import requests
from PIL import Image
from aiogram import types

# Бесплатный OCR.Space ключ для теста
API_KEY = "helloworld"
OCR_URL = "https://api.ocr.space/parse/image"


async def extract_text_from_telegram_photo(bot, file_id: str, max_mb=1) -> str:
    """
    Получает file_id фотографии из Telegram
    Сжимает до max_mb, если нужно, и возвращает распознанный текст через OCR.Space
    """
    # 1. Получаем файл
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    image_bytes = file_bytes.read()

    # 2. Проверяем размер
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        # Сжимаем через Pillow
        image = Image.open(io.BytesIO(image_bytes))
        image.thumbnail((1024, 1024))  # максимальный размер 1024x1024 пикселей
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=70)  # качество 70%
        image_bytes = output.getvalue()

    # 3. Отправляем в OCR.Space
    files = {"file": ("image.jpg", image_bytes)}
    data = {
        "apikey": API_KEY,
        "language": "rus,eng",
        "isOverlayRequired": False
    }

    response = requests.post(OCR_URL, files=files, data=data)
    result = response.json()

    try:
        text = result["ParsedResults"][0]["ParsedText"]
    except (KeyError, IndexError):
        text = "❌ Не удалось распознать текст"

    return text.strip()
