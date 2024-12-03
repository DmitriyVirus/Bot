import asyncio
from aiogram import Bot, Dispatcher, Router
from tgbot.handlers import router as handlers_router
from tgbot.handler_sbor import router as handler_sbor_router
from config import config  # Токен бота

router = Router()
router.include_router(handlers_router)  # Включаем обработчики из tgbot/handlers.py
router.include_router(handler_sbor_router)  # Включаем обработчики из tgbot/handler_sbor.py

class TGBot:
    def __init__(self, router: Router) -> None:
        token = config('TOKEN')
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
