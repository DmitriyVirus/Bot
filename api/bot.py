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
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

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
    try:
        sheet = client.open("quiz").get_worksheet(1)  # Второй лист
        sheet.append_row([name, difficulty])
        print(f"Data saved: {name}, {difficulty}")
    except Exception as e:
        print(f"Error saving data: {e}")
        raise

@app.post("/api/start-quiz", response_class=JSONResponse)
async def start_quiz(user_data: UserData):
    try:
        client = get_gspread_client()  # Получаем клиент для работы с Google Sheets
        if not client:
            raise HTTPException(status_code=500, detail="Google Sheets client is not initialized")

        # Сохраняем данные пользователя на второй вкладке таблицы
        save_user_data(client, user_data.name, user_data.difficulty)

        # Возвращаем успешный ответ с указанием маршрута
        return {"message": "Починаємо!", "redirect_to": "/quiz-start"}

    except Exception as e:
        print(f"Error in start_quiz: {e}")
        return {"status": "error", "message": str(e)}

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
        is_correct = (user_answer.strip().lower() == correct_answer.strip().lower())

        # Работаем с таблицей пользователя
        user_sheet = client.open("quiz").get_worksheet(1)  # Второй лист (индекс 1)
        user_rows = user_sheet.get_all_values()

        last_row_index = len(user_rows)  # Индекс последней строки
        last_row = user_rows[-1] if last_row_index > 1 else [""] * 13

        # Проверяем заполненность столбцов 1-10 (индексы 2-11)
        filled_answers = [value for value in last_row[2:12] if value != ""]
        if len(filled_answers) >= 10:
            # Если все столбцы заполнены, пересчитываем результат и сохраняем
            final_score = sum(int(value) for value in filled_answers if value.isdigit())
            user_sheet.update_cell(last_row_index, 13, final_score)  # Обновляем столбец Result

            export_results_to_static(client)

            # Перенаправляем на страницу с результатами
            return RedirectResponse(url="/quiz-results", status_code=303)

        # Если не все столбцы заполнены, обновляем следующий
        for i in range(2, 12):  # Индексы столбцов 3-12
            if len(last_row) <= i or last_row[i] == "":
                # Вставляем 1 или 0 в первый пустой столбец
                user_sheet.update_cell(last_row_index, i + 1, 1 if is_correct else 0)
                return {
                    "status": "success",
                    "is_correct": is_correct,
                    "correct_answer": correct_answer
                }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/quiz-results", include_in_schema=False)
async def quiz_results():
    return FileResponse("static/quiz_results.html")


def export_results_to_static(client):
    try:
        # Открываем второй лист с результатами
        user_sheet = client.open("quiz").get_worksheet(1)  # Второй лист
        all_rows = user_sheet.get_all_values()

        # Генерируем HTML-код для таблицы
        html_table = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Результаты викторины</title>
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f4f4f4;
                }
            </style>
        </head>
        <body>
            <h1>Результаты викторины</h1>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Difficulty</th>
                        <th>1</th>
                        <th>2</th>
                        <th>3</th>
                        <th>4</th>
                        <th>5</th>
                        <th>6</th>
                        <th>7</th>
                        <th>8</th>
                        <th>9</th>
                        <th>10</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
        """
        for row in all_rows[1:]:  # Пропускаем заголовок
            html_table += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        html_table += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Сохраняем файл в папку static
        with open("static/quiz_results.html", "w", encoding="utf-8") as file:
            file.write(html_table)

        print("Результаты успешно экспортированы в static/quiz_results.html")

    except Exception as e:
        print(f"Ошибка экспорта результатов: {e}")
