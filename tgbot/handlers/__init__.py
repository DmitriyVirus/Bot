# Импортируем все роутеры из отдельных файлов
from .menu import router as menu_router
from .triggers import router as triggers_router
from .greetings import router as greetings_router
from aiogram import Router

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(menu_router)
router.include_router(triggers_router)
router.include_router(greetings_router)
