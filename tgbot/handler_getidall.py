import re
import logging
from aiogram.types import Message
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
import json
from decouple import config
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tgbot.__init__ import tgbot  # Импортируем объект бота из bot_init.py

# Инициализация Google Sheets
creds_json = config('GOOGLE_SHEETS_CREDENTIALS')
creds_dict = json.loads(creds_json)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open('ourid').sheet1  # Укажите название вашей таблицы

# Функция для добавления строки в таблицу Google Sheets
def append_row_to_sheet(user_id, user_name):
    sheet.append_row([user_id, user_name])

# Обработчик сообщений
@router.message()
async def handle_message(message: types.Message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        # Записываем информацию в Google Sheets синхронно
        append_row_to_sheet(user_id, user_name)

        # Логируем информацию
        print(f"Added user {user_name} (ID: {user_id}) to Google Sheets.")

        # Ответ в чат
        await message.reply(f"Спасибо, {user_name}, за сообщение!")
    except Exception as e:
        print(f"Error adding user to Google Sheets: {e}")

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

CHAT_ID = -1001408912941  # Замените на ID вашего чата
PINNED_MESSAGE_ID = 280567  # Замените на ID закрепленного сообщения

@router.message(Command(commands=["getidbot"]))
async def send_message_with_id(message: types.Message):
    try:
        allowed_user_id = 559273200
        if message.from_user.id != allowed_user_id:
            return
            
        sent_message = await message.answer("Получаю id.")
        message_id = sent_message.message_id
        updated_text = f"ID этого сообщения: {message_id}"
        await sent_message.edit_text(updated_text)
        logging.info(f"Текст обновлен. ID сообщения: {message_id}")

    except Exception as e:
        logging.error(f"Ошибка при отправке или редактировании сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

# Обработчик команды /getid
@router.message(Command(commands=["getid"]))
async def send_chat_id(message: Message):
    try:
        allowed_user_id = 559273200 
        if message.from_user.id != allowed_user_id:
            return
        chat_id = message.chat.id
        await message.answer(f"Ваш Chat ID: `{chat_id}`", parse_mode="Markdown")
        logging.info(f"Chat ID ({chat_id}) отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке Chat ID: {e}")
        
@router.message()
async def update_message_text(message: types.Message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        user_info = f"{user_id} - {user_name}"

        # Получаем текст нужного закрепленного сообщения
        current_text = await get_pinned_message_by_id(message.bot, CHAT_ID, PINNED_MESSAGE_ID)

        if current_text is None:
            logging.error("Не удалось найти сообщение с указанным ID.")
            return

        # Проверяем, есть ли пользователь в тексте
        user_pattern = re.compile(r"\d+ - .+")
        users_in_message = user_pattern.findall(current_text)

        if user_info not in users_in_message:
            # Дописываем информацию о пользователе
            updated_text = f"{current_text}\n{user_info}".strip()

            # Обновляем текст сообщения
            await message.bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=PINNED_MESSAGE_ID,
                text=updated_text
            )
            logging.info("Текст сообщения обновлен.")
        else:
            logging.info("Информация уже есть в сообщении. Обновление не требуется.")

    except TelegramBadRequest as e:
        logging.error(f"Ошибка Telegram: {e}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {type(e).__name__}: {e}")


async def get_pinned_message_by_id(bot, chat_id, pinned_message_id):
    """
    Ищет закрепленное сообщение с указанным ID и возвращает его текст.
    """
    try:
        chat = await bot.get_chat(chat_id)
        if chat.pinned_message and chat.pinned_message.message_id == pinned_message_id:
            return chat.pinned_message.text

        # Если закреплено несколько сообщений, пробуем проверить их ID
        messages = await bot.get_chat_pinned_messages(chat_id)
        for message in messages:
            if message.message_id == pinned_message_id:
                return message.text

        logging.error("Сообщение с указанным ID не найдено среди закрепленных.")
        return None
    except TelegramBadRequest as e:
        logging.error(f"Ошибка при получении закрепленных сообщений: {e}")
        return None
