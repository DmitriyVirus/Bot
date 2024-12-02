import logging
import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.triggers import TRIGGERS, WELCOME_TEXT, HELP_TEXT_HEADER, COMMANDS_LIST

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
        
        welcome_text = f"⚡⚡⚡Привет, *{new_member.first_name}*! Теперь ты часть команды.⚡⚡⚡ {WELCOME_TEXT}"
        try:
            await message.answer(welcome_text, parse_mode="Markdown")
            logging.info(f"Отправлено приветствие для {new_member.first_name} (ID: {new_member.id})")
        except TelegramBadRequest as e:
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
    goodbye_text = f"Прощай, {left_member.first_name}! Мы НЕ будем скучать по тебе.👋"
    try:
        await message.answer(goodbye_text)
        logging.info(f"Отправлено прощание для {left_member.first_name} (ID: {left_member.id})")
    except TelegramBadRequest as e:
        logging.error(f"Ошибка при отправке прощания для {left_member.first_name}: {e}")

# Словарь для хранения пользователей, которые нажали кнопку "+"
user_reactions = {}

# Обработчик команды /fix
@router.message(Command(commands=["fix"]))
async def fix_handler(message: Message):
    try:
        # Создаем кнопку
        plus_button = InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_plus")
        # Добавляем кнопку в разметку
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[plus_button]])

        # Отправляем сообщение с кнопкой
        sent_message = await message.answer("Тест", reply_markup=keyboard)
        await sent_message.pin()
        user_reactions.clear()

        # Безопасный запуск фоновой задачи
        asyncio.create_task(manage_fix_message(sent_message, message))
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /fix: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")



async def manage_fix_message(sent_message: Message, command_message: Message):
    try:
        logging.info("Начало работы manage_fix_message")
        # Ждем 60 секунд перед удалением сообщения
        await asyncio.sleep(60)
        logging.info("Таймер завершен, удаляем сообщение")

        try:
            await sent_message.delete()
            logging.info("Сообщение успешно удалено")
        except TelegramBadRequest:
            logging.warning("Не удалось удалить сообщение (возможно, оно уже удалено)")

        # Обрабатываем пользователей
        joined_in_limit = list(user_reactions.values())[:5]
        left_out = list(user_reactions.values())[5:]

        if joined_in_limit:
            await command_message.answer(f"В фулку вошли: {', '.join(joined_in_limit)}")
            logging.info(f"Сообщено о пользователях в фулке: {', '.join(joined_in_limit)}")
        if left_out:
            await command_message.answer(f"Также плюсовали: {', '.join(left_out)}")
            logging.info(f"Сообщено о пользователях вне фулки: {', '.join(left_out)}")
    except Exception as e:
        logging.error(f"Ошибка при управлении сообщением: {e}")

# Обработчик callback для кнопки "+"
@router.callback_query(lambda callback: callback.data == "join_plus")
async def handle_plus_reaction(callback):
    user_id = callback.from_user.id
    if user_id not in user_reactions:
        user_reactions[user_id] = callback.from_user.first_name
        await callback.answer("Вы присоединились!")
        reaction_count = len(user_reactions)

        sent_message = callback.message
        updated_text = f"Тест\n\nКоличество участников: {reaction_count}"

        # Проверка, изменился ли текст перед обновлением
        if sent_message.text != updated_text:
            await sent_message.edit_text(updated_text, reply_markup=sent_message.reply_markup)

        if reaction_count == 5:
            updated_text = f"Тест\n\nУже фулка! ({', '.join(user_reactions.values())})"
            # Проверка, изменился ли текст перед обновлением
            if sent_message.text != updated_text:
                await sent_message.edit_text(updated_text, reply_markup=None)
    else:
        await callback.answer("Вы уже присоединились!")

        
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

# Обработчик команды /bye1
@router.message(Command(commands=["bye1"]))  # Используем фильтр Command
async def dno_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIDIGdK0OJwj31wUKdAUgxygDBJs2IdAAL3WAACVk5YSsQhdK_UudsRNgQ"  # Ваш file_id
    try:
        # Отправляем видео с использованием file_id
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")

# Обработчик команды /bye2
@router.message(Command(commands=["bye2"]))  # Используем фильтр Command
async def dno_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIDI2dLDIjfeiMQ55Ae8yv-GzRHfSnZAAIzXAACVk5YSlsGnAdQnVQ7NgQ"  # Ваш file_id
    try:
        # Отправляем видео с использованием file_id
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")
        
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

# Обработчик команды /help
@router.message(Command(commands=["help"]))
async def help_handler(message: Message):
    help_text = "*Доступные команды:*\n\n"
    # Добавляем все команды из COMMANDS_LIST
    for command in COMMANDS_LIST:
        help_text += f"{command}\n"
    await message.answer(help_text, parse_mode="Markdown")

# Обработчик команды /getid
@router.message(Command(commands=["getid"]))
async def send_chat_id(message: Message):
    try:
        # Получаем ID чата
        chat_id = message.chat.id
        # Отправляем ID чата пользователю
        await message.answer(f"Ваш Chat ID: `{chat_id}`", parse_mode="Markdown")
        logging.info(f"Chat ID ({chat_id}) отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке Chat ID: {e}")
        
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
