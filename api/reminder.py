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
        
        if day_of_week in [0, 1, 2, 3, 4]:
            # Создание объекта Message
            message = types.Message(
                message_id=1234,  # Поставьте подходящий id
                from_user=types.User(id=12345, is_bot=False, first_name="Bot", last_name="Botov", username="botov_user"),  # Создание пользователя
                chat=types.Chat(id=config('CHAT_ID'), type='private'),  # Здесь нужно указать ID чата, в котором будет происходить отправка сообщения
                date=datetime.datetime.now(),
                text="/inst 19:30"  # Текст с командой, которую нужно передать в хендлер
            )
            
            # Создаем объект Update
            update = types.Update(
                update_id=123456789,  # Уникальный ID для обновления
                message=message  # Добавляем сообщение в объект Update
            )

            # Передаем обновление в Dispatcher с использованием feed_update
            await tgbot.dp.feed_update(update)  # Обрабатываем обновление через feed_update
            return {"status": "success", "message": "Reminder sent"}
        else:
            return {"status": "skipped", "message": "Not a reminder day"}
    
    except Exception as e:
        logging.error(f"Ошибка при отправке напоминания: {e}")
        return {"status": "error", "message": str(e)}
