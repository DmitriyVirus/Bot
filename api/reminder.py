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

# Функция для отправки напоминания
async def send_reminder1():
     try:
        # Параметры команды
        chat_id = config('CHAT_ID')
        command_text = "/inst 19:30"
        
        # Создаём фейковое сообщение для передачи в хендлер
        fake_message = Message(
            message_id=123,  # Идентификатор сообщения (можно указать любое значение)
            from_user=User(id=12345, is_bot=True, first_name="Bot"),  # Данные бота как отправителя
            chat=Chat(id=chat_id, type="private"),  # Данные чата, куда отправляется сообщение
            date=datetime.datetime.now(),
            text=command_text
        )
        
        # Вызываем хендлер напрямую, передавая созданное сообщение
        await fix_handler(fake_message)
        
        return {"status": "success", "message": "Command processed by handler"}
    except Exception as e:
        logging.error(f"Ошибка при обработке команды: {e}")
        return {"status": "error", "message": str(e)}
