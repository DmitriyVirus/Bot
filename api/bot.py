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

@app.get("/quiz-start", include_in_schema=False)
async def quiz_start_page():
    return FileResponse(os.path.join(os.getcwd(), "static", "quiz-start.html"))

# Модель для ответа пользователя
class UserAnswer(BaseModel):
    name: str
    question_id: int
    user_answer: str

import random

@app.get("/api/get-question")
async def get_question(name: str):
    client = get_gspread_client()
    question_sheet = client.open("quiz").sheet1  # Первый лист с вопросами
    user_sheet = client.open("quiz").get_worksheet(1)  # Второй лист с пользователями

    # Найти пользователя
    user_records = user_sheet.get_all_records()
    user_row = None
    for i, record in enumerate(user_records):
        if record["Name"] == name:
            user_row = i + 2  # +2 для учета заголовков
            break

    if user_row is None:
        return {"status": "error", "message": "User not found."}

    # Найти первый незавершенный вопрос
    for question_id in range(1, 16):  # Вопросы от 1 до 15
        if not user_sheet.cell(user_row, question_id + 2).value:  # Проверка пустой ячейки
            question_row = question_sheet.row_values(question_id + 1)  # +1 для учета заголовков
            question_text = question_row[1]
            correct_answer = question_row[2]

            # Получить все ответы из столбца C (правильные ответы)
            all_answers = question_sheet.col_values(3)[1:]  # Исключаем заголовок
            all_answers = list(set(all_answers) - {correct_answer})  # Убираем правильный ответ

            # Выбираем 3 случайных ответа
            wrong_answers = random.sample(all_answers, min(len(all_answers), 3))
            options = [correct_answer] + wrong_answers
            random.shuffle(options)  # Перемешиваем варианты

            return {
                "status": "success",
                "question_id": question_id,
                "question": question_text,
                "options": options
            }

    # Если вопросы закончились
    return {"status": "completed", "message": "Викторина завершена. Спасибо за участие!"}

# Проверка ответа и обновление прогресса
@app.post("/api/submit-answer")
async def submit_answer(data: UserAnswer):
    client = get_gspread_client()
    question_sheet = client.open("quiz").sheet1  # Первый лист с вопросами
    user_sheet = client.open("quiz").get_worksheet(1)  # Второй лист с пользователями

    # Найти пользователя
    records = user_sheet.get_all_records()
    for i, record in enumerate(records):
        if record["Name"] == data.name:
            # Проверяем ответ
            correct_answer = question_sheet.cell(data.question_id + 1, 3).value
            is_correct = 1 if data.user_answer == correct_answer else 0

            # Обновляем таблицу
            user_sheet.update_cell(i + 2, data.question_id + 2, is_correct)  # +2 из-за заголовков
            return {"result": "Correct" if is_correct else "Incorrect"}

    raise HTTPException(status_code=404, detail="User not found.")
