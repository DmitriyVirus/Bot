# api/quiz.py
import os
import random
import json
from tgbot.gspread_client import get_gspread_client  # Импортируем функцию из gspread_client

# Получаем все вопросы из таблицы
def fetch_questions_from_sheet(client):
    sheet = client.open("quiz").sheet1
    records = sheet.get_all_records()
    questions = []
    for record in records:
        question = {
            "id": record["id"],
            "question": record["question"],
            "correct_answer": record["answer"],
        }
        questions.append(question)
    return questions

# Генерация случайных вариантов ответов
def generate_answers(client, correct_answer):
    # Получаем все возможные ответы
    sheet = client.open("quiz").sheet1
    all_answers = sheet.col_values(3)[1:]  # Получаем все ответы из столбца "answer", исключая заголовок
    all_answers = list(set(all_answers) - {correct_answer})  # Убираем правильный ответ

    # Выбираем 3 неправильных ответа случайным образом
    wrong_answers = random.sample(all_answers, 3)
    
    # Перемешиваем правильный и неправильные ответы
    answers = [correct_answer] + wrong_answers
    random.shuffle(answers)
    
    return answers

# Функция для получения вопроса и вариантов ответов
async def get_question(question_id):
    client = get_gspread_client()  # Получаем клиент для работы с Google Sheets
    if not client:
        raise Exception("Google Sheets client is not initialized")

    question_data = get_question_and_answers(client, question_id)
    return {
        "question": question_data["question"],
        "answers": question_data["answers"],
        "correct_answer": question_data["correct_answer"]
    }

# Функция для проверки ответа
async def check_answer(question_id, user_answer):
    client = get_gspread_client()
    if not client:
        raise Exception("Google Sheets client is not initialized")

    question_data = get_question_and_answers(client, question_id)
    correct_answer = question_data["correct_answer"]

    if user_answer == correct_answer:
        return {"result": "Correct!"}
    else:
        return {"result": "Incorrect!"}

# Пример использования (можно удалить после тестирования)
def get_question_and_answers(client, question_id):
    questions = fetch_questions_from_sheet(client)
    question = next((q for q in questions if q["id"] == question_id), None)

    if not question:
        raise ValueError("Question not found")

    correct_answer = question["correct_answer"]
    answers = generate_answers(client, correct_answer)

    return {
        "question": question["question"],
        "answers": answers,
        "correct_answer": correct_answer
    }

# Функция для сохранения ответа в Google Sheets
def save_answer_to_sheet(client, name, difficulty, question_id, user_answer, correct_answer):
    sheet = client.open("quiz").sheet1
    # Найдем строку для данного пользователя и сложности
    user_row = None
    for i, record in enumerate(sheet.get_all_records()):
        if record["Name"] == name and record["Difficulty"] == difficulty:
            user_row = i + 2  # Индекс строки (с учетом заголовка)
            break
    
    if not user_row:
        raise Exception("Не найден пользователь с такой сложностью")

    # Сравниваем ответ с правильным и сохраняем 1 (правильный ответ) или 0 (неправильный)
    is_correct = 1 if user_answer == correct_answer else 0
    question_column = str(question_id)  # Номер столбца - вопрос
    sheet.update_cell(user_row, int(question_column) + 2, is_correct)  # Обновляем результат

