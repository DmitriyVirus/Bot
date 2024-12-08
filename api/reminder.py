import os
import random
import logging
import datetime
from tgbot import tgbot
from aiogram import types
from decouple import config
from aiogram.types import Message, User, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

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

async def send_reminder1_route(request: Request):
    try:
        # Основная логика отправки фото
        photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
        keyboard = create_keyboard()
        chat_id = config('CHAT_ID')

        sent_message = await tgbot.bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=(
                f"☠️*Идем в инсты 19:30*.☠️\n\nКак обычно идут Дмитрий(МакароноВирус), Леонид(ТуманныйТор) и кто-то еще. Есть 5 мест.\n\n"
                f"⚡⚡⚡*Нажмите ➕ в сообщении для участия*⚡⚡⚡"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        # Закрепление сообщения
        await tgbot.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)
        logging.info(f"Сообщение отправлено и закреплено с id: {sent_message.message_id}")
        return {"status": "success", "message": "Сообщение отправлено и закреплено"}
    except Exception as e:
        logging.error(f"Ошибка при обработке команды: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])

