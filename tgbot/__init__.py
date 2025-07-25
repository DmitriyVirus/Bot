import os
import asyncio
from config import config  # Используем конфигурацию для токена
from aiogram import Bot, Dispatcher, Router
from tgbot.handlers import router as handlers_router # Убедитесь, что импортируете router из handlers
from tgbot.handler_sbor import router as handler_sbor_router
from tgbot.handler_getidall import router as handler_getidall_router
from tgbot.google_sheets import router as google_sheets_router  # Импорт функции добавления пользователя
from tgbot.google_sheets import add_user_to_sheet, fetch_data_from_sheet  # Импорт функции добавления пользователя
from tgbot.gspread_client import get_gspread_client

router = Router()
router.include_router(handlers_router)  # Подключаем хендлеры
router.include_router(handler_sbor_router)
router.include_router(handler_getidall_router)
router.include_router(google_sheets_router)


class TGBot:
    def __init__(self, router: Router) -> None:
        token = os.getenv('TOKEN')
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.dp.include_router(router)  # Подключаем роутер
        self.webhook_url = config('WEBHOOK_URL')

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)
        print(f"Webhook set to {self.webhook_url}")

# Инициализация tgbot с импортированным router
tgbot = TGBot(router)

