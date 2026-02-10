# Импортируем все роутеры из отдельных файлов
from .autoget import router as autoget_router
from .adminka import router as adminka_router
from .gspread_client import get_gspread_client
from .autoget import add_user_to_sheet
from aiogram import Router

# Импортируем функции для работы с Google Sheets
from .take_from_sheet import (
    get_info_column_by_header,
    get_bot_commands,
    get_bot_deb_cmd,
    fetch_participants,
    get_admins_records
)

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(adminka_router)
router.include_router(autoget_router)

