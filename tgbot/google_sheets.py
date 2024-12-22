import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.errors import HttpError

# Получаем JSON-ключ из переменной окружения
creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')

# Преобразуем JSON-строку в словарь
creds_dict = json.loads(creds_json)

# Подключаемся к Google Sheets с использованием сервисного аккаунта
def connect_to_google_sheets():
    try:
        # Используем OAuth2 для подключения к Google API
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except HttpError as err:
        print(f"Failed to connect to Google Sheets: {err}")
        return None

def add_user_to_sheet(user_id: int, username: str):
    # Подключаемся к Google Sheets
    client = connect_to_google_sheets()
    
    if client is None:
        print("Google Sheets connection failed.")
        return
    
    try:
        # Открываем таблицу по имени (например, "ourid")
        sheet = client.open("ourid").sheet1
        
        # Добавляем данные в таблицу
        sheet.append_row([user_id, username])
        print(f"User {username} (ID: {user_id}) added to Google Sheets.")
    except gspread.exceptions.SpreadsheetNotFound as e:
        print(f"Spreadsheet not found: {e}")
    except gspread.exceptions.APIError as e:
        print(f"API Error occurred while writing to the sheet: {e}")
