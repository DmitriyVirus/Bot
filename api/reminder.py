import os
import random
import logging
import datetime
from tgbot import tgbot
from aiogram import types
from decouple import config
from tgbot.handler_sbor import fix_handler

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

# Пример исправления для вызова хендлера с передачей команды /inst
async def send_reminder1():
    try:
        # Получаем текущий день недели (0 - понедельник, 1 - вторник, ..., 6 - воскресенье)
        day_of_week = datetime.datetime.now().weekday()
        # Проверяем, что день недели - понедельник (0), вторник (1), среда (2) или четверг (3)
        if day_of_week in [0, 1, 2, 3, 4]:
            # Создаем message, чтобы передать его в диспетчер
            message = types.Message(
                message_id=1234,  # Поставьте подходящий id
                from_user=types.User(id=12345, is_bot=False, first_name="Bot", last_name="Botov", username="botov_user"),  # Создание пользователя
                chat=types.Chat(id=config('CHAT_ID'), type='private'),  # ID чата
                date=datetime.datetime.now(),
                text="/inst 19:30"  # Текст с командой
            )

            # Вызов хендлера с использованием диспетчера
            await tgbot.dp.process_update(types.Update(message=message))  # Обработка update с использованием dispatcher
            return {"status": "success", "message": "Reminder sent"}
        else:
            return {"status": "skipped", "message": "Not a reminder day"}
    except Exception as e:
        logging.error(f"Ошибка при отправке напоминания: {e}")
        return {"status": "error", "message": str(e)}

