import json
import logging
from tgbot import tgbot
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI()

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Обработка favicon
@app.get("/favicon.png", include_in_schema=False)
@app.head("/favicon.png", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/favicon.png")

# Функция для отправки напоминания
async def send_reminder():
    try:
        message = "Напоминание: время 14:40! 🌟"
        # Отправка сообщения в Telegram
        await tgbot.bot.send_message(chat_id=-1002388880478, text=message)
        logging.info(f"Сообщение отправлено: {message}")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

# Установка webhook при старте
@app.on_event("startup")
async def on_startup():
    try:
        print("Setting webhook...")
        await tgbot.set_webhook()

        # Настроим планировщик и добавим задачу
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            send_reminder,  # Задача для напоминания
            trigger='cron',  # Используем cron
            hour=14,  # Час (14:00)
            minute=40,  # Минуты (40)
            second=0  # Секунды (0)
        )
        # Запуск планировщика
        scheduler.start()

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
    return {"message": "Привет, мир!"}

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

