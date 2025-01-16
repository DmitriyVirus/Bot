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

# Пример использования
def get_question_and_answers(client, question_id):
    # Получаем все вопросы
    questions = fetch_questions_from_sheet(client)
    question = next((q for q in questions if q["id"] == question_id), None)

    if not question:
        raise ValueError("Вопрос не найден")

    correct_answer = question["correct_answer"]
    answers = generate_answers(client, correct_answer)

    return {
        "question": question["question"],
        "answers": answers,
        "correct_answer": correct_answer
    }

# Получаем клиента для работы с Google Sheets
client = get_gspread_client()

# Получаем вопрос и ответы для вопроса с id = 1
question_data = get_question_and_answers(client, 1)

print("Вопрос:", question_data["question"])
print("Ответы:", question_data["answers"])
print("Правильный ответ:", question_data["correct_answer"])

