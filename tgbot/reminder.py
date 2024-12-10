import datetime
import os
import random
import logging
from aiogram import types, Router
from aiogram.filters import Command
from config import config  # Убедитесь, что ваш config правильно настроен

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# Хендлер для команды /goodmornigeverydayGG
@router.message(Command(commands=["goodmornigeverydayGG"]))
async def good_mornig_every_day_GG(message: types.Message):
    try:
        text = "Всем доброго утра! Рабочий день начинается!"
        file_path = os.path.join(os.getcwd(), "urls", "mond_url.txt")
    
        # Загрузка ссылок из файла
        with open(file_path, "r") as file:
            photo_urls = file.readlines()

        # Выбор случайной ссылки
        photo_url = random.choice(photo_urls).strip()  # Убираем лишние пробелы или символы новой строки
        
        # Отправка текста и фото
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=text,
            parse_mode="Markdown"
        )

        return {"status": "success", "message": "Reminder sent"}

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /goodmornigeverydayGG: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
        return {"status": "error", "message": str(e)}
