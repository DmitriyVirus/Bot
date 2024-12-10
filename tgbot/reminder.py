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
        # Получаем текущий день недели
        day_of_week = datetime.datetime.now().weekday()
        
        # Логика для дней недели
        if day_of_week == 0:  # Понедельник
            text = "Утро добрым не бывает, а понедельник ведь все-таки день тяжелый... Но не унываем!"
            file_path = os.path.join(os.getcwd(), "urls", "mond_url.txt")
        elif day_of_week in [1, 2, 3]:  # Вторник, Среда, Четверг
            text = "Всем доброго утра! Рабочий день начинается!"
            file_path = os.path.join(os.getcwd(), "urls", "workdays_url.txt")
        elif day_of_week == 4:  # Пятница
            text = "Всем доброго утра! А вот вы знали, что сегодня пятница?!"
            file_path = os.path.join(os.getcwd(), "urls", "fri_url.txt")
        elif day_of_week in [5, 6]:  # Выходные
            text = "Всем доброго утра! Выхходные! Гуляеммм!!!"
            file_path = os.path.join(os.getcwd(), "urls", "weekend_url.txt")
        else:
            return {"status": "skipped", "message": "Not a reminder day"}

        # Проверка существования файла
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден.")

        # Загрузка ссылок из файла
        with open(file_path, "r") as file:
            photo_urls = file.readlines()

        # Проверка, что список не пуст
        if not photo_urls:
            raise ValueError(f"Файл {file_path} пуст.")

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
