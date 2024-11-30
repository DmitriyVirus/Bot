import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from tgbot.triggers import TRIGGERS, WELCOME_TEXT, HELP_TEXT_HEADER

router = Router()

# Приветствие новых пользователей
@router.message(lambda message: hasattr(message, 'new_chat_members') and message.new_chat_members)
async def greet_new_members(message: Message):
    logging.info(f"Получено событие добавления новых участников: {message.new_chat_members}")
    for new_member in message.new_chat_members:
        if new_member.is_bot:
            logging.info(f"Пропущен бот: {new_member}")
            continue
        logging.info(f"Формируется приветствие для {new_member.first_name} (ID: {new_member.id})")
        
        # Используем текст из triggers.py и подставляем имя пользователя
        welcome_text = f"⚡⚡⚡Привет, *{new_member.first_name}*! Теперь ты часть команды.⚡⚡⚡ {WELCOME_TEXT}"
        try:
            await message.answer(welcome_text, parse_mode="Markdown")  # Указываем режим Markdown
            logging.info(f"Отправлено приветствие для {new_member.first_name} (ID: {new_member.id})")
        except Exception as e:
            logging.error(f"Ошибка при отправке приветствия {new_member.first_name}: {e}")

# Прощание с пользователями
@router.message(lambda message: hasattr(message, 'left_chat_member') and message.left_chat_member)
async def say_goodbye(message: Message):
    logging.info(f"Получено событие удаления участника: {message.left_chat_member}")
    left_member = message.left_chat_member
    if left_member.is_bot:
        logging.info(f"Пропущен бот: {left_member}")
        return
    logging.info(f"Формируется прощание для {left_member.first_name} (ID: {left_member.id})") 
    goodbye_text = f"Прощай, {left_member.first_name}! Мы НЕ будем скучать по тебе. Если передумаешь, обратно не пустим! 👋"
    try:
        await message.answer(goodbye_text)
        logging.info(f"Отправлено прощание для {left_member.first_name} (ID: {left_member.id})")
        await message.answer_video("BAACAgIAAxkBAAIDIGdK0OJwj31wUKdAUgxygDBJs2IdAAL3WAACVk5YSsQhdK_UudsRNgQ")
    except Exception as e:
        logging.error(f"Ошибка при отправке прощания для {left_member.first_name}: {e}")

# Обработчик команды /fu
@router.message(Command(commands=["fu"]))  # Используем фильтр Command
async def fu_handler(message: Message):
    # Пример того, как можно использовать триггер из TRIGGERS
    trigger = "код красный тут матюки"  # Триггер, на который будет реагировать команда /fu
    if trigger in TRIGGERS:
        response = TRIGGERS[trigger]  # Получаем ответ для триггера
        # Если ответ это строка (текст)
        if isinstance(response, str):
            await message.answer(response, parse_mode="Markdown")      
        # Если ответ это словарь с ключами 'text', 'image', 'gif'
        elif isinstance(response, dict):
            if "text" in response:
                await message.answer(response["text"], parse_mode="Markdown")
            if "image" in response:
                await message.answer_photo(response["image"])
            if "gif" in response:
                await message.answer_animation(response["gif"])
    else:
        await message.answer("Нет ответа для этой команды.", parse_mode="Markdown")

# Обработчик команды /nakol
@router.message(Command(commands=["nakol"]))  # Используем фильтр Command
async def fu_handler(message: Message):
    # Пример того, как можно использовать триггер из TRIGGERS
    trigger = "на кол посадить"  # Триггер, на который будет реагировать команда /fu
    if trigger in TRIGGERS:
        response = TRIGGERS[trigger]  # Получаем ответ для триггера
        # Если ответ это строка (текст)
        if isinstance(response, str):
            await message.answer(response, parse_mode="Markdown")      
        # Если ответ это словарь с ключами 'text', 'image', 'gif'
        elif isinstance(response, dict):
            if "text" in response:
                await message.answer(response["text"], parse_mode="Markdown")
            if "image" in response:
                await message.answer_photo(response["image"])
            if "gif" in response:
                await message.answer_animation(response["gif"])
    else:
        await message.answer("Нет ответа для этой команды.", parse_mode="Markdown")

# Обработчик команды /dno
@router.message(Command(commands=["dno"]))  # Используем фильтр Command
async def dno_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIDImdK3qVe2zCyGZNxRMPeWUL6DL5lAAJlWQACVk5YSrZ9OPVNhsglNgQ"  # Ваш file_id
    try:
        # Отправляем видео с использованием file_id
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")

# Обработчик команды /hi
@router.message(Command(commands=["hi"]))
async def send_welcome(message: Message):
    try:
        # Отправляем WELCOME_TEXT с Markdown-разметкой
        await message.answer(WELCOME_TEXT, parse_mode="Markdown")
    except Exception as e:
        # Логируем ошибку, если не удалось отправить сообщение
        logging.error(f"Ошибка при отправке приветствия: {e}")
        
# Обработчик команды /bot
@router.message(Command(commands=["bot"]))  # Используем фильтр Command
async def help_handler(message: Message):
    help_text = HELP_TEXT_HEADER    
    # Перебираем триггеры и нумеруем их
    for i, trigger in enumerate(TRIGGERS, 1):
        trigger_text = trigger.split(":")[0]  # Извлекаем часть до символа ":" или оставляем сам текст, если ":" нет
        trigger_text = trigger_text.capitalize()  # Преобразуем первую букву в верхний регистр
        help_text += f"{i}. {trigger_text}\n"  # Добавляем номер и фразу
    
    await message.answer(help_text, parse_mode="Markdown")

# Обрабатываем Триггеры
@router.message(lambda message: message.text and any(trigger in message.text.lower() for trigger in TRIGGERS))
async def trigger_handler(message: Message):
    message_text = message.text.lower()
    for trigger, response in TRIGGERS.items():
        if trigger in message_text:
            if isinstance(response, dict):
                if "text" in response:
                    await message.answer(response["text"], parse_mode="Markdown")
                if "image" in response:
                    try:
                        await message.answer_photo(response["image"])
                    except Exception as e:
                        logging.error(f"Ошибка при отправке изображения: {e}")
                if "gif" in response:
                    try:
                        await message.answer_animation(response["gif"])
                    except Exception as e:
                        logging.error(f"Ошибка при отправке GIF: {e}")
            else:
                await message.answer(response, parse_mode="Markdown")
            break
