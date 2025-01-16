import os
import json
from tgbot import tgbot
from decouple import config
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Router, types
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from tgbot.gspread_client import get_gspread_client

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

# Страница викторины
@app.get("/quiz", include_in_schema=False)
async def quiz_page():
    return FileResponse(os.path.join(os.getcwd(), "static", "quiz.html"))

# Модель для данных пользователя (имя и сложность)
class UserData(BaseModel):
    name: str
    difficulty: str

# Функция для сохранения данных пользователя в Google Sheets
def save_user_data(client, name, difficulty):
    sheet = client.open("quiz").get_worksheet(1)  # Второй лист
    sheet.append_row([name, difficulty])

@app.post("/api/start-quiz", response_class=JSONResponse)
async def start_quiz(user_data: UserData):
    client = get_gspread_client()  # Получаем клиент для работы с Google Sheets
    if not client:
        raise Exception("Google Sheets client is not initialized")

    # Сохраняем данные пользователя на второй вкладке таблицы
    save_user_data(client, user_data.name, user_data.difficulty)

    # Возвращаем успешный ответ с указанием маршрута
    return {"message": "Данные успешно сохранены. Викторина начинается!", "redirect_to": "/quiz-start"}

@app.post("/api/start-quiz", response_class=JSONResponse)
async def start_quiz(user_data: UserData):
    client = get_gspread_client()  # Получаем клиент для работы с Google Sheets
    if not client:
        raise Exception("Google Sheets client is not initialized")

    # Сохраняем данные пользователя на второй вкладке таблицы
    save_user_data(client, user_data.name, user_data.difficulty)

    # Возвращаем успешный ответ с указанием маршрута
    return {"message": "Данные успешно сохранены. Викторина начинается!", "redirect_to": "/quiz-start"}

@app.get("/quiz-start", include_in_schema=False)
async def quiz_start_page(request: Request):
    user_name = localStorage.getItem("userName")  # Получаем имя из localStorage
    return FileResponse(os.path.join(os.getcwd(), "static", "quiz-start.html"))

