# Импортируем все роутеры из отдельных файлов
from .autoget import router as autoget_router
from .gspread_client import get_gspread_client
from .autoget import add_user_to_sheet
from aiogram import Router

# Импортируем функции для работы с Google Sheets
from .take_from_sheet import (
    get_bot_commands,
    get_bot_deb_cmd,
    fetch_participants,
    get_welcome_text,
    get_hello_text,
    get_about_bot_text,
    get_image_from_cell,
    get_admins_records
)

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(autoget_router)
