import os
import json
import random
from decouple import config
from pydantic import BaseModel
from aiogram import Bot, Router, types
from fastapi.staticfiles import StaticFiles
from tgbot.gspread_client import get_gspread_client
from fastapi import APIRouter, FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse

router = APIRouter()

# Модель для данных пользователя (имя и сложность)
class UserData(BaseModel):
    name: str
    difficulty: str

class AnswerCheck(BaseModel):
    question: str  # Текст вопроса
    user_answer: str  # Ответ пользователя

# Функция для сохранения данных пользователя в Google Sheets
def save_user_data(client, name, difficulty):
    try:
        sheet = client.open("quiz").get_worksheet(1)  # Второй лист
        sheet.append_row([name, difficulty])
        print(f"Data saved: {name}, {difficulty}")
    except Exception as e:
        print(f"Error saving data: {e}")
        raise

# Главная страница викторины
@router.get("/game_alexandr", include_in_schema=False)
async def game_alexandr_page():
    return HTMLResponse(
        content=open(os.path.join(os.getcwd(), "Quiz", "game_alexandr.html"), "r").read(),
        status_code=200
    )
          
# Страница викторины
@router.get("/quiz", include_in_schema=False)
async def quiz_page():
    return FileResponse(os.path.join(os.getcwd(), "Quiz", "quiz.html"))

@router.post("/api/start-quiz", response_class=JSONResponse)
async def start_quiz(user_data: UserData):
    try:
        client = get_gspread_client()  # Получаем клиент для работы с Google Sheets
        if not client:
            raise HTTPException(status_code=500, detail="Google Sheets client is not initialized")

        # Сохраняем данные пользователя на второй вкладке таблицы
        save_user_data(client, user_data.name, user_data.difficulty)

        # Возвращаем успешный ответ с указанием маршрута
        return {"message": "Починаємо!", "redirect_to": "/quiz_start"}

    except Exception as e:
        print(f"Error in start_quiz: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/quiz_start", include_in_schema=False)
async def quiz_start_page(request: Request):
    return FileResponse(os.path.join(os.getcwd(), "Quiz", "quiz_start.html"))

@router.get("/api/get-question")
async def get_question():
    try:
        client = get_gspread_client()  # Получаем клиент для работы с Google Sheets
        if not client:
            raise HTTPException(status_code=500, detail="Не удалось подключиться к Google Sheets.")

        # Получаем второй лист, где хранятся настройки сложности
        settings_sheet = client.open("quiz").get_worksheet(1)  # Второй лист
        all_settings = settings_sheet.get_all_values()

        if not all_settings:
            raise HTTPException(status_code=500, detail="Невизначений рівень.")

        # Получаем последнюю строку данных (последнего пользователя)
        last_row = all_settings[-1]  # Получаем последнюю строку

        # Получаем сложность из последней строки (предполагается, что она в 2-м столбце)
        difficulty = last_row[1]  # Сложность во втором столбце

        # Маппинг сложности
        difficulty_dict = {
            "Легко": 2,        # 2 неправильных ответа
            "Нормально": 3,    # 3 неправильных ответа
            "Важко": 5,       # 5 неправильных ответов
            "Serious": 0   # Требуется вручную вводить ответ
        }

        wrong_answer_count = difficulty_dict.get(difficulty, 3)  # Если сложность не найдена, берем 3

        # Получаем первый лист с вопросами
        question_sheet = client.open("quiz").sheet1  # Первый лист с вопросами

        # Получаем все строки с вопросами и ответами, начиная с 2-й строки
        all_rows = question_sheet.get_all_values()[1:]  # Пропускаем первую строку, которая может быть заголовком

        if not all_rows:
            return {"status": "error", "message": "Нет данных в таблице"}

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

@router.post("/api/check-answer-and-update")
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
        is_correct = (user_answer.strip().lower() == correct_answer.strip().lower())

        # Работаем с таблицей пользователя
        user_sheet = client.open("quiz").get_worksheet(1)  # Второй лист (индекс 1)
        user_rows = user_sheet.get_all_values()

        if len(user_rows) < 2:  # Если данных нет (только заголовки)
            raise HTTPException(status_code=400, detail="Нет данных о пользователях.")

        # Индекс последней строки
        last_row_index = len(user_rows)
        last_row = user_rows[-1]

        # Проверяем заполненность столбцов с ответами (столбцы 3-12)
        filled_answers = [value for value in last_row[2:12] if value]
        if len(filled_answers) >= 10:
            # Подсчет итогового результата
            final_score = sum(int(value) for value in filled_answers if value.isdigit())
            user_sheet.update_cell(last_row_index, 13, final_score)  # Обновляем итоговый результат
            return {
                "status": "success",
                "finished": True,
                "message": "Викторина завершена!",
            }

        # Находим первый незаполненный столбец
        for i in range(2, 12):  # Столбцы 3-12
            if len(last_row) <= i or not last_row[i]:
                user_sheet.update_cell(last_row_index, i + 1, 1 if is_correct else 0)
                return {
                    "status": "success",
                    "finished": False,
                    "is_correct": is_correct,
                    "correct_answer": correct_answer,
                }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/quiz-results", response_class=HTMLResponse)
async def quiz_results():
    try:
        return FileResponse(os.path.join(os.getcwd(), "Quiz", "quiz_results.html"))
    except Exception as e:
        print(f"Error: {e}")
        return HTMLResponse(
            "<h1>Произошла ошибка при загрузке страницы результата. Попробуйте позже.</h1>",
            status_code=500
        )

@router.get("/api/quiz-table-data", response_class=JSONResponse)
async def quiz_table_data():
    try:
        client = get_gspread_client()
        if not client:
            return {"status": "error", "message": "Не удалось подключиться к Google Sheets."}

        # Открываем таблицу пользователей
        user_sheet = client.open("quiz").get_worksheet(1)  # Второй лист (индекс 1)
        user_rows = user_sheet.get_all_values()

        if len(user_rows) <= 1:  # Если данных нет (только заголовки)
            return {"status": "error", "message": "Нет данных для отображения."}

        # Пропускаем первую строку (заголовки)
        user_rows = user_rows[1:]

        # Фильтруем строки, чтобы оставить только те, где есть текст
        filtered_rows = [
            row for row in user_rows
            if any(cell.strip() for cell in row)  # Оставляем строки, где есть хотя бы одно непустое значение
        ]

        if not filtered_rows:
            return {"status": "error", "message": "Нет данных для отображения."}

        # Извлекаем только 1-й, 2-й и 13-й столбцы (индексы 0, 1 и 12)
        extracted_data = [
            [row[0], row[1], int(row[12]) if len(row) > 12 and row[12].isdigit() else 0]
            for row in filtered_rows
        ]

        # Сортируем по значению 13-го столбца (от большего к меньшему)
        sorted_data = sorted(extracted_data, key=lambda x: x[2], reverse=True)

        # Получаем последние 10 строк
        top_10_data = sorted_data[:10]

        # Получаем последнюю строку таблицы (не по сортировке, а именно из таблицы)
        last_user_row = filtered_rows[-1] if filtered_rows else None
        last_user_result = {
            "name": last_user_row[0] if len(last_user_row) > 0 else "N/A",
            "difficulty": last_user_row[1] if len(last_user_row) > 1 else "N/A",
            "score": int(last_user_row[12]) if len(last_user_row) > 12 and last_user_row[12].isdigit() else 0,
        } if last_user_row else None

        return {
            "status": "success",
            "table_data": top_10_data,
            "last_user_result": last_user_result,
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/quiz_log")
async def quiz_log_page():
    try:
        # Замените путь на нужный путь для вашего HTML-файла
        content = open("static/quiz_log.html", "r").read()
        return HTMLResponse(content=content, status_code=200)
    except Exception as e:
        # Возвращаем ошибку, если не удалось загрузить страницу
        return HTMLResponse(f"<h1>Error loading page: {e}</h1>", status_code=500)
