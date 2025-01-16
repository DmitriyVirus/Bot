import os
import json
import random
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
    return FileResponse(os.path.join(os.getcwd(), "static", "quiz-start.html"))

@app.get("/api/get-question")
async def get_question():
    try:
        client = get_gspread_client()  # Получаем клиент для работы с Google Sheets
        if not client:
            raise HTTPException(status_code=500, detail="Не удалось подключиться к Google Sheets.")

        # Получаем второй лист, где хранятся настройки сложности
        settings_sheet = client.open("quiz").get_worksheet(1)  # Второй лист
        all_settings = settings_sheet.get_all_values()

        if not all_settings:
            raise HTTPException(status_code=500, detail="Нет данных о сложности в таблице.")

        # Получаем последнюю строку данных (последнего пользователя)
        last_row = all_settings[-1]  # Получаем последнюю строку

        # Получаем сложность из последней строки (предполагается, что она в 2-м столбце)
        difficulty = last_row[1]  # Сложность во втором столбце

        # Маппинг сложности
        difficulty_dict = {
            "Легко": 2,        # 2 неправильных ответа
            "Нормально": 3,    # 3 неправильных ответа
            "Сложно": 5,       # 5 неправильных ответов
            "Апокалипсис": 0   # Требуется вручную вводить ответ
        }

        wrong_answer_count = difficulty_dict.get(difficulty, 3)  # Если сложность не найдена, берем 3

        # Получаем первый лист с вопросами
        question_sheet = client.open("quiz").sheet1  # Первый лист с вопросами

        # Получаем все строки с вопросами и ответами, начиная с 2-й строки
        all_rows = question_sheet.get_all_values()[1:]  # Пропускаем первую строку, которая может быть заголовком

        if not all_rows:
            return {"status": "error", "message": "Нет данных в таблице."}

        # Выбираем случайную строку
        random_row = random.choice(all_rows)

        question_text = random_row[1]  # Второй столбец - текст вопроса
        correct_answer = random_row[2]  # Третий столбец - правильный ответ

        # Собираем все варианты ответов (включая правильный)
        all_answers = random_row[2:]  # Все ответы (правильный и возможные неправильные)
        wrong_answers = [answer for answer in all_answers if answer != correct_answer]  # Убираем правильный ответ

        # Ограничиваем количество неправильных вариантов в зависимости от сложности
        wrong_answers = wrong_answers[:wrong_answer_count]

        if wrong_answer_count > 0:
            # Собираем варианты ответов
            options = [correct_answer] + wrong_answers
            random.shuffle(options)  # Перемешиваем варианты

            return {
                "status": "success",
                "question_id": 1,
                "question": question_text,
                "options": options
            }
        else:
            # Для сложности "Апокалипсис" возвращаем запрос на ввод ответа вручную
            return {
                "status": "manual_input",
                "question_id": 1,
                "question": question_text,
                "correct_answer": correct_answer
            }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

class AnswerCheck(BaseModel):
    question: str  # Текст вопроса
    user_answer: str  # Ответ пользователя

@app.post("/api/check-answer", response_class=JSONResponse)
async def check_answer(answer_check: AnswerCheck):
    try:
        client = get_gspread_client()
        if not client:
            raise HTTPException(status_code=500, detail="Не удалось подключиться к Google Sheets.")
        
        # Открываем лист с вопросами
        question_sheet = client.open("quiz").sheet1
        all_rows = question_sheet.get_all_values()[1:]  # Пропускаем заголовок

        # Ищем вопрос по тексту (2-й столбец)
        matching_question = next((row for row in all_rows if row[1].strip().lower() == answer_check.question.strip().lower()), None)
        if not matching_question:
            return {"status": "error", "message": "Вопрос не найден."}
        
        # Получаем правильный ответ (3-й столбец)
        correct_answer = matching_question[2]
        is_correct = answer_check.user_answer.strip().lower() == correct_answer.strip().lower()

        return {
            "status": "success",
            "is_correct": is_correct,
            "correct_answer": correct_answer
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/check-answer-and-update")
async def check_answer_and_update(data: dict):
    try:
        question = data.get("question")
        user_answer = data.get("user_answer")

        if not question or not user_answer:
            raise HTTPException(status_code=400, detail="Некорректные данные.")

        client = get_gspread_client()
        if not client:
            raise HTTPException(status_code=500, detail="Не удалось подключиться к Google Sheets.")

        # Получаем первый лист с вопросами
        question_sheet = client.open("quiz").sheet1
        all_rows = question_sheet.get_all_values()[1:]  # Пропускаем заголовок

        # Ищем строку с текстом вопроса
        question_row = next((row for row in all_rows if row[1] == question), None)
        if not question_row:
            return {"status": "error", "message": "Вопрос не найден."}

        correct_answer = question_row[2]  # Третий столбец - правильный ответ
        is_correct = (user_answer == correct_answer)

        # Работаем с таблицей пользователя
        user_sheet = client.open("quiz").get_worksheet(1)
        user_rows = user_sheet.get_all_values()

        if not user_rows:
            raise HTTPException(status_code=500, detail="Нет данных о пользователях.")

        last_user_row = user_rows[-1]  # Последняя строка
        for i in range(2, 12):  # Проверяем столбцы 3-12
            if last_user_row[i] == "":
                user_sheet.update_cell(len(user_rows), i + 1, 1 if is_correct else 0)  # Обновляем значение
                return {
                    "status": "success",
                    "is_correct": is_correct,
                    "correct_answer": correct_answer
                }

        # Если все столбцы заполнены, возвращаем итоговый результат
        final_score = last_user_row[12]  # 13-й столбец
        return {
            "status": "success",
            "finished": True,
            "final_score": final_score
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

