import os
import shutil
import datetime
import zipfile
import requests
import json
from aiogram import Router, types
from aiogram.filters import Command
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

router = Router()

TEMP_DIR = "/tmp/Backup"
GITHUB_REPO_URL = "https://github.com/DmitriyVirus/Bot"
BACKUP_FOLDER_ID = os.getenv("BACKUP_FOLDER_ID")
GOOGLE_KEY = os.getenv("GOOGLE_SHEET_KEY")


def download_repo_zip():
    """Скачивает репозиторий GitHub в ZIP и распаковывает в TEMP_DIR"""
    zip_url = GITHUB_REPO_URL.rstrip('/') + "/archive/refs/heads/main.zip"
    zip_path = "/tmp/repo.zip"

    # Скачиваем архив
    r = requests.get(zip_url, stream=True)
    r.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    # Чистим TEMP_DIR и создаем заново
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    # Распаковываем архив
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)

    # Папка с распакованным репозиторием
    extracted_folder = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
    return extracted_folder


def create_archive(folder_path):
    """Создает ZIP архива из папки"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    archive_name = f"/tmp/bot_backup_{timestamp}.zip"
    shutil.make_archive(archive_name.replace('.zip', ''), 'zip', folder_path)
    return archive_name


def upload_to_gdrive(archive_path):
    """Загружает архив на Google Drive в папку BACKUP_FOLDER_ID"""
    if not GOOGLE_KEY:
        raise ValueError("GOOGLE_SHEET_KEY is missing")
    if not BACKUP_FOLDER_ID:
        raise ValueError("BACKUP_FOLDER_ID is missing")

    creds = Credentials.from_service_account_info(
        json.loads(GOOGLE_KEY),
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    drive_service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(archive_path),
        'parents': [BACKUP_FOLDER_ID]
    }
    media = MediaFileUpload(archive_path, mimetype='application/zip')

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"Файл загружен на Google Drive, ID: {file['id']}")


def cleanup(archive_path):
    """Удаляет временные файлы"""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if os.path.exists("/tmp/repo.zip"):
        os.remove("/tmp/repo.zip")
    if os.path.exists(archive_path):
        os.remove(archive_path)


@router.message(Command("backupbotnow"))
async def backup_now(message: types.Message):
    await message.answer("Начинаю бэкап репозитория...")
    try:
        # Скачиваем репозиторий
        repo_folder = download_repo_zip()

        # Создаем архив
        archive_path = create_archive(repo_folder)

        # Загружаем на Google Drive
        upload_to_gdrive(archive_path)

        # Чистим временные файлы
        cleanup(archive_path)

        await message.answer("✅ Бэкап успешно создан и загружен на Google Диск!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при бэкапе: {e}")
