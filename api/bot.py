import json
import logging
from tgbot import tgbot
from pytz import timezone
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI()

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Обработка favicon
@app.get("/favicon.png", include_in_schema=False)
@app.head("/favicon.png", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/favicon.png")
     
# Часовой пояс для Украины
ukraine_tz = timezone("Europe/Kyiv")

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

# Главная страница с текущим временем
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def read_root():
    # Время на сервере (в часовом поясе сервера)
    server_time = datetime.now()
    formatted_server_time = server_time.strftime("%Y-%m-%d %H:%M:%S")
    # Время в вашей тайм-зоне (Европа/Киев)
    ukraine_time = datetime.now(ukraine_tz)
    formatted_ukraine_time = ukraine_time.strftime("%Y-%m-%d %H:%M:%S")
    # Возвращаем оба времени
    return {
        "message": "Привет, мир!",
        "server_time": f"Время на сервере: {formatted_server_time}",
        "ukraine_time": f"Время в Украине: {formatted_ukraine_time}"
    }
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

@app.get("/api/bot/cron")
async def cron_job():
    message = "Сегодня рабочий день у всех"
    await tgbot.bot.send_message(chat_id=-1002388880478, text=message)  # Ваш чат ID
    return {"status": "success"}
