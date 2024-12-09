import os
import json
from tgbot import tgbot
from decouple import config
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Router, types
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.reminder import send_reminder, send_reminder1

app = FastAPI()

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    try:
        logging.info("Setting webhook...")
        await tgbot.set_webhook()
        logging.info("Webhook successfully set.")
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("Shutting down...")
    await tgbot.bot.session.close()
    logging.info("Bot session closed.")

@app.get('/send_reminder/{reminder_type}', include_in_schema=False)
async def send_reminder_route(reminder_type: str):
    try:
        if reminder_type == "1":
            asyncio.create_task(send_reminder1())
            return {"status": "success", "message": "Reminder 1 task started"}
        elif reminder_type == "2":
            asyncio.create_task(send_reminder())
            return {"status": "success", "message": "Reminder 2 task started"}
        else:
            raise HTTPException(status_code=400, detail="Invalid reminder type")
    except Exception as e:
        logging.error(f"Error in send_reminder_route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

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
