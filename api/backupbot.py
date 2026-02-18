import os
import shutil
import datetime
import zipfile
import requests
import json
from fastapi import APIRouter
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

router = APIRouter()

TEMP_DIR = "/tmp/Backup"
ARCHIVE_DIR = "/tmp/archives"  # сюда складываем архивы
GITHUB_REPO_URL = "https://github.com/DmitriyVirus/Bot"
BACKUP_FOLDER_ID = os.getenv("BACKUP_FOLDER_ID")
GOOGLE_KEY = os.getenv("GOOGLE_SHEET_KEY")
MAX_ARCHIVES = 14  # лимит архивов

os.makedirs(ARCHIVE_DIR, exist_ok=True)


def download_repo_zip():
    """Скачивает репозиторий GitHub в ZIP и распаковывает в TEMP_DIR"""
    zip_url = GITHUB_REPO_URL.rstrip('/') + "/archive/refs/heads/main.zip"
    zip_path = "/tmp/repo.zip"

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

    extracted_folder = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
    return extracted_folder


def create_archive(folder_path):
    """Создает ZIP архива из папки с форматом времени по Украине"""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))  # UTC+2
    timestamp = now.strftime("%d_%m_%Y_%H_%M")
    archive_name = os.path.join(ARCHIVE_DIR, f"Bot_{timestamp}.zip")
    shutil.make_archive(archive_name.replace('.zip', ''), 'zip', folder_path)
    return archive_name


def upload_to_gdrive(archive_path):
    """Загружает архив на Google Drive"""
    if not GOOGLE_KEY or not BACKUP_FOLDER_ID:
        raise ValueError("Не задан GOOGLE_SHEET_KEY или BACKUP_FOLDER_ID")

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


def cleanup_temp(archive_path):
    """Удаляет временные файлы"""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if os.path.exists("/tmp/repo.zip"):
        os.remove("/tmp/repo.zip")
    if os.path.exists(archive_path):
        os.remove(archive_path)


def cleanup_old_archives():
    """Удаляет старые архивы, если больше MAX_ARCHIVES"""
    archives = sorted(
        [os.path.join(ARCHIVE_DIR, f) for f in os.listdir(ARCHIVE_DIR)],
        key=os.path.getmtime
    )
    while len(archives) > MAX_ARCHIVES:
        os.remove(archives[0])
        archives.pop(0)


def backup_repo():
    """Полный цикл бэкапа"""
    repo_folder = download_repo_zip()
    archive_path = create_archive(repo_folder)
    upload_to_gdrive(archive_path)
    cleanup_temp(archive_path)
    cleanup_old_archives()


# =========================
# FastAPI endpoint для cron
# =========================
@router.get("/api/cron/backup")
async def cron_backup():
    try:
        backup_repo()
        return {"status": "ok", "message": "Бэкап выполнен"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
