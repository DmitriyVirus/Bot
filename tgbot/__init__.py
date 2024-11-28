import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.exceptions import TelegramRetryAfter

class TGBot:
    def __init__(self, router: Router) -> None:
        self.bot = Bot(token=config('TOKEN'))
        self.webhook_url = config('WEBHOOK_URL')

    async def update_bot(self, update: dict) -> None:
        try:
            await self.bot.process_update(update)
        except Exception as e:
            print(f"Error updating bot: {e}")
        finally:
            await self.bot.session.close()

    async def set_webhook(self):
        retries = 5
        for _ in range(retries):
            try:
                await self.bot.set_webhook(self.webhook_url)
                print(f"Webhook set to {self.webhook_url}")
                break
            except TelegramRetryAfter as e:
                print(f"Rate limit exceeded, retrying in {e.retry_after} seconds...")
                await asyncio.sleep(e.retry_after)
            except Exception as e:
                print(f"Error setting webhook: {e}")
                break

tgbot = TGBot(router)
