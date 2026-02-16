# Импортируем все роутеры из отдельных файлов
from .redis_cash import router as redis_cas_router
from aiogram import Router

# Создаём единый роутер для всех хэндлеров
router = Router()
router.include_router(redis_cas_router)
