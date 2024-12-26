# gspread_client.py
import json
import os
import logging
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)

# Получаем ключ из переменной окружения
creds_json = os.getenv('GOOGLE_SHEET_KEY')

def get_gspread_client():
    """
    Возвращает клиент для работы с Google Sheets.
    """
    try:
        if not creds_json:
            logging.error("Google Sheets API key is missing. Set GOOGLE_SHEET_KEY environment variable.")
            return None

        credentials = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(credentials)
        logging.info("Google Sheets API authentication successful.")
        return client
    except Exception as e:
        logging.error(f"Error while authenticating with Google Sheets API: {e}")
        return None
