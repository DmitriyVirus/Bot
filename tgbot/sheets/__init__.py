# Импортируем все роутеры из отдельных файлов
from .autoget import router as autoget_router
from .autoget import add_user_to_sheet
from aiogram import Router

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(autoget_router)
