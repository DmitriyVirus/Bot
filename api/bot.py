import os
import json
from tgbot import tgbot
from decouple import config
from datetime import datetime
from aiogram.types import Chat
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Router, types
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tgbot.handler_sbor import fix_handler
from api.reminder import send_reminder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
app = FastAPI()

# Монтируем директорию для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Установка webhook при старте
@app.on_event("startup")
async def on_startup():
    try:
        print("Setting webhook...")
        await tgbot.set_webhook()
    except Exception as e:
        print(f"Error setting webhook: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    await tgbot.bot.session.close()
    print("Bot session closed.")

# Главная страница
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def read_root():
    return FileResponse(os.path.join(os.getcwd(), "index.html"))

# Обработка webhook-запросов от Telegram
@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    try:
        update_dict = await request.json()
        print("Received update:", json.dumps(update_dict, indent=4))  # Логирование обновления
        await tgbot.update_bot(update_dict)
        return ''
    except Exception as e:
        print(f"Error processing update: {e}")
        return {"error": str(e)}

@app.post("/send_reminder1")
async def send_reminder1_route(request: Request):
    try:
        # Попытка чтения тела запроса
        try:
            payload = await request.json()
        except Exception as e:
            logging.error(f"Ошибка при чтении тела запроса: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")

        # Проверка содержимого
        if not payload:
            logging.error("Тело запроса пустое.")
            return {"status": "error", "message": "Request body is empty"}

        # Извлечение команды
        command = payload.get("text", "").strip()
        if not command:
            logging.error("Текст команды отсутствует в запросе.")
            return {"status": "error", "message": "Missing 'text' in request"}

        logging.info(f"Получен текст команды: {command}")

        # Основная логика
        if command.lower() == "старт":
            photo_url = "https://battleclub.space/uploads/monthly_2022_07/baylor.jpg.02e0df864753bf47b1ef76303b993a1d.jpg"
            keyboard = create_keyboard()
            chat_id = config('CHAT_ID')

            # Отправляем фото
            sent_message = await tgbot.bot.send_photo(
                chat_id=chat_id,
                photo=photo_url,
                caption=(f"☠️*Идем в инсты 19:30*.☠️\n\nКак обычно идут участники. Есть 5 мест."),
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            # Закрепляем сообщение
            await tgbot.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)
            logging.info(f"Сообщение отправлено с ID: {sent_message.message_id}")

            return {"status": "success", "message": f"Сообщение отправлено и закреплено, ID: {sent_message.message_id}"}
        else:
            return {"status": "error", "message": "Неизвестная команда"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logging.error(f"Ошибка при обработке команды: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
        
# Вызов функции отправки первого напоминания
@app.get('/send_reminder', include_in_schema=False)
async def send_reminder_route():
    return await send_reminder()  # Используем функцию из reminder.py

# Функция для создания клавиатуры
def create_keyboard():
    plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
    minus_button = InlineKeyboardButton(text="➖ Не участвовать", callback_data="join_minus")
    return InlineKeyboardMarkup(inline_keyboard=[[plus_button, minus_button]])
