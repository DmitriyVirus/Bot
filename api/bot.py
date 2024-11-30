import os
import json
import random
import logging
import datetime
from tgbot import tgbot
from decouple import config
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

app = FastAPI()

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Установка webhook при старте
@app.on_event("startup")
async def on_startup():
    try:
        print("Setting webhook...")
        await tgbot.set_webhook()
    except Exception as e:
        print(f"Error setting webhook: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    await tgbot.bot.session.close()
    print("Bot session closed.")

# Главная страница
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def read_root():
    return FileResponse(os.path.join(os.getcwd(), "static", "index.html"))
   
# Обработка webhook-запросов от Telegram
@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    try:
        update_dict = await request.json()
        print("Received update:", json.dumps(update_dict, indent=4))  # Логирование обновления
        await tgbot.update_bot(update_dict)
        return ''
    except Exception as e:
        print(f"Error processing update: {e}")
        return {"error": str(e)}

# Обработка favicon
@app.get("/favicon.png", include_in_schema=False)
@app.head("/favicon.png", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(os.getcwd(), "static", "favicon.ico"))

@app.get('/send_reminder', include_in_schema=False)
async def send_reminder():
    try:
        # Получаем текущий день недели
        day_of_week = datetime.datetime.now().weekday()
        
        # Логика для дней недели
        if day_of_week in [0]:  # Понедельник
            text = "Утро добрым не бывает, а понедельник ведь все-таки день тяжелый... Но не унываем!"  
            file_path = os.path.join(os.getcwd(), "static", "mond_url.txt")
        elif day_of_week in [1, 2, 3]:  # Вторник, Среда, Четверг
            text = "Всем доброго утра! Рабочий день начинается!"
            file_path = os.path.join(os.getcwd(), "static", "workdays_url.txt")
        elif day_of_week in [4]:  # Пятница
            text = "Всем доброго утра! А вот вы знали, что сегодня пятница?!"
            file_path = os.path.join(os.getcwd(), "static", "fri_url.txt")
        elif day_of_week in [5, 6]:  # Выходные
            text = "Всем доброго утра! Выхходные! Гуляеммм!!!"
            file_path = os.path.join(os.getcwd(), "static", "weekend_url.txt")
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

@app.get('/send_reminder1', include_in_schema=False)
async def send_reminder():
    try:
        # Получаем текущий день недели (0 - понедельник, 1 - вторник, ..., 6 - воскресенье)
        day_of_week = datetime.datetime.now().weekday()
        # Проверяем, что день недели - понедельник (0), вторник (1), среда (2) или четверг (3)
        if day_of_week in [0, 1, 2, 3, 4]:
            text = "Значится идем на инсты как обычно в 19:30. Иду Я, Тор и еще кто-то. Ставим + в ответ на мое сообщение, чтобы я видел кто будет участвовать. Если не вижу, то пните меня."
            photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
            # Отправка текста и фото
            await tgbot.bot.send_photo(chat_id=config('CHAT_ID'), photo=photo_url, caption=text)
            return {"status": "success", "message": "Reminder sent"}
        else:
            return {"status": "skipped", "message": "Not a reminder day"}
    except Exception as e:
        logging.error(f"Ошибка при отправке напоминания: {e}")
        return {"status": "error", "message": str(e)}
        
