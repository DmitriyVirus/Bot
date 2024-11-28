import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Update
from tgbot.handlers import router
from config import config  # Используем конфигурацию для токена

class TGBot:
    def __init__(self, router: Router) -> None:
        token = config('TOKEN')
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.dp.include_router(router)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.set_webhook())

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()
        
     async def set_webhook(self) -> None:
        await self.bot.set_webhook(self.webhook_url)

tgbot = TGBot(router)
