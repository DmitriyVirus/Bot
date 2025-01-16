import os
from tgbot.gspread_client import get_gspread_client  # Импортируем функцию из gspread_client

# Функция для сохранения данных пользователя в Google Sheets
def save_user_data(client, name, difficulty):
    sheet = client.open("quiz").get_worksheet(1)  # Второй лист
    sheet.append_row([name, difficulty])
