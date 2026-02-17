import os
import asyncio
from aiogram import Bot, Dispatcher, Router
from tgbot.handlers import router as handlers_router
from tgbot.sheets import router as sheets_router
from tgbot.redis import router as redis_router


router = Router()
router.include_router(handlers_router)
router.include_router(sheets_router)
router.include_router(redis_router)


class TGBot:
    def __init__(self, router: Router) -> None:
        token = os.getenv("TOKEN")
        webhook_url = os.getenv("WEBHOOK_URL")

        if not token:
            raise RuntimeError("TOKEN не задан в переменных окружения")
        if not webhook_url:
            raise RuntimeError("WEBHOOK_URL не задан в переменных окружения")

        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.dp.include_router(router)
        self.webhook_url = webhook_url

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()

    async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)
        print(f"Webhook set to {self.webhook_url}")


tgbot = TGBot(router)









