import os
import json
from tgbot import tgbot
from decouple import config
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.reminder import send_reminder
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
    return FileResponse(os.path.join(os.getcwd(), "index.html"))

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

@app.post("/send_reminder1")
async def handle_pipedream_webhook(request: Request):
    try:
        payload = await request.json()  # Получаем данные из тела запроса
        # Понимание команды из запроса
        if 'command' in payload and payload['command'] == 'inst 19:30':
            # Здесь вы вызываете вашу функцию для команды /inst
            message = types.Message()  # Создайте объект message, если это необходимо
            await fix_handler(message)
            return {"status": "Command executed"}
        else:
            return {"status": "Invalid command"}
    except Exception as e:
        logging.error(f"Error handling webhook: {e}")
        return {"status": "Error", "message": str(e)}
        
# Вызов функции отправки первого напоминания
@app.get('/send_reminder', include_in_schema=False)
async def send_reminder_route():
    return await send_reminder()  # Используем функцию из reminder.py

# Вызов функции отправки второго напоминания
@app.get('/send_reminder1', include_in_schema=False)
async def send_reminder1_route():
    return await send_reminder1()  # Используем новую функцию из reminder.py

