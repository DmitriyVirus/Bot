import json
import logging
from tgbot import tgbot
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)

try:
    scheduler = AsyncIOScheduler()
    logging.info("AsyncIOScheduler создан успешно.")
except Exception as e:
    logging.error(f"Ошибка при создании AsyncIOScheduler: {e}")
    
app = FastAPI()

# Получите ID чата, куда будут отправляться сообщения
CHAT_ID = -1002388880478  

# Функция для отправки сообщения
async def send_daily_message():
    message = "Доброе утро! 🌅 Начинаем новый день!"
    try:
        await tgbot.bot.send_message(CHAT_ID, message)
        logging.info(f"Сообщение отправлено: {message}")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Обработка favicon
@app.get("/favicon.png", include_in_schema=False)
@app.head("/favicon.png", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/favicon.png")

# Установка webhook при старте
@app.on_event("startup")
async def on_startup():
    try:
        print("Setting webhook...")
        await tgbot.set_webhook()

        # Настроим планировщик и добавим задание
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            send_daily_message,
            trigger='cron',  # Используем cron
            hour=13,  # Час (12:00)
            minute=10,  # Минуты (50)
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
