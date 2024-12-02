import os
import random
import logging
import datetime
from tgbot import tgbot
from decouple import config

async def send_reminder():
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

        # Загрузка ссылок из файла
        with open(file_path, "r") as file:
            photo_urls = file.readlines()

        # Выбор случайной ссылки
        photo_url = random.choice(photo_urls).strip()  # Убираем лишние пробелы или символы новой строки
        
        # Отправка текста и фото
        await tgbot.bot.send_photo(chat_id=config('CHAT_ID'), photo=photo_url, caption=text)
        return {"status": "success", "message": "Reminder sent"}

    except Exception as e:
        logging.error(f"Ошибка при отправке напоминания: {e}")
        return {"status": "error", "message": str(e)}

async def send_reminder1():
    try:
        # Получаем текущий день недели (0 - понедельник, 1 - вторник, ..., 6 - воскресенье)
        day_of_week = datetime.datetime.now().weekday()
        
        # Проверяем, что день недели - понедельник (0), вторник (1), среда (2) или четверг (3)
        if day_of_week in [0, 1, 2, 3, 4]:
            text = """Значится идем на инсты как обычно в 19:30.
Иду Я, Тор и еще кто-то.
Ставим + в ответ на мое сообщение, чтобы я видел кто будет участвовать.
Если не вижу, то пните меня."""
            photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
            # Отправка текста и фото
            await tgbot.bot.send_photo(chat_id=config('CHAT_ID'), photo=photo_url, caption=text)
            return {"status": "success", "message": "Reminder sent"}
        else:
            return {"status": "skipped", "message": "Not a reminder day"}

    except Exception as e:
        logging.error(f"Ошибка при отправке напоминания: {e}")
        return {"status": "error", "message": str(e)}
