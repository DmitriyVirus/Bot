import os
import asyncio
from config import config
from aiogram import Bot, Dispatcher, Router

from tgbot.handlers import routers  # Список роутеров: menu_router, greetings_router, triggers_router
from tgbot.handler_sbor import router as handler_sbor_router
from tgbot.handler_getidall import router as handler_getidall_router
from tgbot.google_sheets import router as google_sheets_router
from tgbot.google_tab import router as google_tab_router

# Главный роутер
router = Router()

# Подключаем роутеры
router.include_router(google_tab_router)
router.include_router(handler_sbor_router)
router.include_router(google_sheets_router)
router.include_router(handler_getidall_router)

# Подключаем стандартные роутеры из handlers
for r in routers:
    router.include_router(r)


# Класс бота
class TGBot:
    def __init__(self, router: Router) -> None:
        token = os.getenv('TOKEN')
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.dp.include_router(router)
        self.webhook_url = config('WEBHOOK_URL')

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)
        print(f"Webhook set to {self.webhook_url}")


# Инициализация tgbot с импортированным router
tgbot = TGBot(router)
