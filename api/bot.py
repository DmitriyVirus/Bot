from fastapi import FastAPI, Request
from tgbot.handlers import send_help, welcome_new_user, text_trigger_handler

app = FastAPI()

@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    update = await request.json()  # Получаем обновление от Telegram

    if "message" in update:
        message = update["message"]

        # Если это новая команда /help
        if "text" in message and message["text"].startswith("/help"):
            await send_help(message)
        
        # Если это сообщение от нового пользователя
        elif "new_chat_members" in message:
            await welcome_new_user(message)
        
        # Обработка текстовых сообщений с триггерами
        elif "text" in message:
            await text_trigger_handler(message)
    
    return ''
