import os
import json
from tgbot import tgbot
from decouple import config
from fastapi import FastAPI, Request
from aiogram import Bot, Router, types
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
        raw_body = await request.body()
        # Вызываем хендлер вручную
        message = types.Message(text=f"/inst 19:30", chat=types.Chat(id=chat_id))
        await fix_handler(message)
        if not raw_body:
            print("Request body is empty.")
            return {"status": "error", "message": "Request body is empty"}
        
        print("Raw body:", raw_body)
        payload = await request.json()
        print("Parsed payload:", payload)
        return {"status": "success", "message": "Payload processed"}
    except json.JSONDecodeError:
        print("Invalid JSON format")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
        
# Вызов функции отправки первого напоминания
@app.get('/send_reminder', include_in_schema=False)
async def send_reminder_route():
    return await send_reminder()  # Используем функцию из reminder.py
