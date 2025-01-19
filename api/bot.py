import os
import json
import random
from tgbot import tgbot
from fastapi import FastAPI
from decouple import config
from pydantic import BaseModel
from aiogram import Bot, Router, types
from fastapi.staticfiles import StaticFiles
from Quiz.quizgame import router as quiz_router
from tgbot.gspread_client import get_gspread_client
from fastapi import FastAPI, Request, HTTPException
from Quiz.quizgame import UserData, AnswerCheck, save_user_data
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse

app = FastAPI()

app.include_router(quiz_router)

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/Quiz", StaticFiles(directory="Quiz"), name="static")
      
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
