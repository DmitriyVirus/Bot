import datetime  # Для работы с датой и временем
import os  # Для работы с файловой системой
import random  # Для случайного выбора ссылки
import logging
from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import Message, User, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.triggers import TRIGGERS, WELCOME_TEXT, HELP_TEXT_HEADER, COMMANDS_LIST, NAME_TABLE, ALIASES, FIRST, ABOUT, DEBUG_BOT
from config import config  # Ваш файл конфигурации с токенами, чатами и другими параметрами

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = Router()

# Список ID администраторов
ADMINS = {1141764502, 559273200}  # Замените на ID ваших администраторов

# ID пользователей, для которых меню ведет себя по-другому
EXCLUDED_USER_IDS = {559273200}  # Замените на нужные ID

# Функции форматирования текстов
def format_commands(commands_list):
    """Форматирует список команд."""
    return "\n".join(commands_list) if commands_list else "Нет доступных команд."

def format_triggers(triggers):
    """Форматирует список триггеров с нумерацией."""
    return (
        "\n".join([f"{i + 1}. {trigger}" for i, trigger in enumerate(triggers.keys())])
        if triggers
        else "Нет доступных триггеров."
    )

def is_excluded_user(user_id: int) -> bool:
    """Проверяет, является ли пользователь исключённым."""
    return user_id in EXCLUDED_USER_IDS

# Функция для создания главного меню
def create_main_menu():
    buttons = [
        [InlineKeyboardButton(text="Команды", callback_data="menu_commands")],
        [InlineKeyboardButton(text="Участники", callback_data="menu_participants")],
        [InlineKeyboardButton(text="Об игре", callback_data="menu_about_game")],
        [InlineKeyboardButton(text="О боте", callback_data="menu_about_bot")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция для создания подменю с одной кнопкой "Назад"
def create_back_menu():
    back_button = InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    return InlineKeyboardMarkup(inline_keyboard=[[back_button]])

# Функция для создания меню команд
def create_commands_menu(is_admin_user: bool):
    main_commands_button = InlineKeyboardButton(text="Основные", callback_data="commands_main")
    back_button = InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    keyboard = [[main_commands_button]]

    # Если пользователь администратор, добавляем кнопку "Отладка"
    if is_admin_user:
        debug_commands_button = InlineKeyboardButton(text="Отладка", callback_data="commands_debug")
        keyboard.append([debug_commands_button])

    keyboard.append([back_button])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Проверка на администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# Обработчик команды /bot
@router.message(Command(commands=["bot"]))
async def bot_command_handler(message: types.Message):
    keyboard = create_main_menu()
    await message.answer(
        FIRST,
        reply_markup=keyboard,
        parse_mode="HTML",  # Активируем HTML-разметку для ссылок
        disable_web_page_preview=True  # Отключаем предпросмотр
    )

# Обработчик для кнопки "Участники"
@router.callback_query(lambda callback: callback.data == "menu_participants")
async def menu_participants_handler(callback: types.CallbackQuery):
    response = "Список всех пользователей:\n"
    for user_name, user_info in NAME_TABLE.items():
        response += (
            f"\nИмя: {user_info['name']}\n"
            f"Имя в телеграмм: {user_info['tgnick']}\n"
            f"Ник: {user_info['nick']}\n"
            f"Инфо: {user_info['about']}\n"
        )
    await callback.message.edit_text(response, reply_markup=create_back_menu())

# Обработчик для кнопки "О боте"
@router.callback_query(lambda callback: callback.data == "menu_about_bot")
async def menu_about_bot_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        ABOUT,
        reply_markup=create_back_menu(),
        parse_mode="HTML",
        disable_web_page_preview=True  # Отключаем предпросмотр ссылок
    )

# Обработчик для кнопки "Основные команды"
@router.callback_query(lambda callback: callback.data == "menu_commands")
async def menu_commands_handler(callback: types.CallbackQuery):
    logger.debug(f"Обработчик {callback.data} вызван пользователем {callback.from_user.id}")
    user_id = callback.from_user.id

    if not is_excluded_user(user_id):
        try:
            keyboard = create_back_menu()
            commands_text = format_commands(COMMANDS_LIST)
            triggers_text = format_triggers(TRIGGERS)

            await callback.message.edit_text(
                f"Основные команды:\n{commands_text}\n\n"
                f"Основные триггеры:\n{triggers_text}",
                reply_markup=keyboard
            )
            logger.debug("Сообщение успешно обновлено.")
        except Exception as e:
            logger.error(f"Ошибка при обработке команды: {e}")
            await callback.message.answer("Произошла ошибка при обработке вашего запроса.")
    else:
        logger.debug(f"Исключённый пользователь с ID {user_id}")
        keyboard = create_commands_menu(is_admin(user_id))
        await callback.message.edit_text("Типы команд:", reply_markup=keyboard)

# Обработчик для кнопки "Отладка"
@router.callback_query(lambda callback: callback.data == "commands_debug")
async def commands_debug_handler(callback: types.CallbackQuery):
    logger.debug(f"Обработчик {callback.data} вызван пользователем {callback.from_user.id}")
    if is_admin(callback.from_user.id):
        keyboard = create_back_menu()
        await callback.message.edit_text(
            f"Отладочные команды:\n{format_commands(DEBUG_BOT)}",
            reply_markup=keyboard
        )
    else:
        await callback.answer("У вас нет прав доступа к этой функции.", show_alert=True)

# Обработчик для кнопки "Основные"
@router.callback_query(lambda callback: callback.data == "commands_main")
async def commands_main_handler(callback: types.CallbackQuery):
    logger.debug(f"Получен callback с данными: {callback.data}")

    try:
        keyboard = create_back_menu()
        commands_text = format_commands(COMMANDS_LIST)
        triggers_text = format_triggers(TRIGGERS)

        await callback.message.edit_text(
            f"Основные команды:\n{commands_text}\n\n"
            f"Основные триггеры:\n{triggers_text}",
            reply_markup=keyboard
        )
        logger.debug("Сообщение успешно обновлено.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении сообщения: {e}")

# Обработчик для кнопки "Назад" (возвращает в главное меню)
@router.callback_query(lambda callback: callback.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    keyboard = create_main_menu()
    await callback.message.edit_text(FIRST, reply_markup=keyboard)
        
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
    goodbye_text = f"Прощай, {left_member.first_name}! Мы НЕ будем скучать по тебе.👋"
    try:
        await message.answer(goodbye_text)
        logging.info(f"Отправлено прощание для {left_member.first_name} (ID: {left_member.id})")
    except Exception as e:
        logging.error(f"Ошибка при отправке прощания для {left_member.first_name}: {e}")

def build_expanded_table(name_table, aliases):
    expanded_table = {}
    for key, value in name_table.items():
        expanded_table[key] = value
        if key in aliases:
            for alias in aliases[key]:
                expanded_table[alias] = value
    return expanded_table

@router.message(Command(commands=["kto"]))
async def who_is_this(message: types.Message):
    # Расширяем таблицу с алиасами для поиска
    expanded_table = build_expanded_table(NAME_TABLE, ALIASES)
    
    # Разделяем команду и аргумент
    args = message.text.split(' ', 1)

    # Если аргумент не указан
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите имя после команды или 'all' для всех.")
        return

    # Получаем введённое имя в нижнем регистре
    name = args[1].strip().lower()

    # Если введено 'all', показываем информацию о всех пользователях (без алиасов)
    if name == "all":
        response = "Список всех пользователей:\n"
        for user_name, user_info in NAME_TABLE.items():  # Используем исходную таблицу без алиасов
            response += f"\nИмя: {user_info['name']}\nИмя в телеграмм: {user_info['tgnick']}\nНик: {user_info['nick']}\nИнфо: {user_info['about']}\n"
        await message.answer(response)
    else:
        # Преобразуем ключи в таблице в нижний регистр для удобства поиска
        expanded_table_lower = {key.lower(): value for key, value in expanded_table.items()}
        
        # Ищем конкретного пользователя в расширенной таблице с алиасами, используя таблицу с нижним регистром
        user_info = expanded_table_lower.get(name)  # Используем таблицу с алиасами в нижнем регистре
        if user_info:
            response = f"Имя: {user_info['name']}\nНик: {user_info['nick']}\nИнфо: {user_info['about']}"
            await message.answer(response)
        else:
            await message.answer(f"Информация о пользователе '{args[1]}' не найдена.")

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

# Обработчик команды /klaar
@router.message(Command(commands=["klaar"]))  # Используем фильтр Command
async def dno_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIDgWdar1ZHi4Baas954WdvLHCKOv35AAIlYAAC3ejZSvIFDXGe8drUNgQ"  # Ваш file_id
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

# Обработчик команды /help
@router.message(Command(commands=["help"]))
async def help_handler(message: Message):
    help_text = "*Доступные команды:*\n\n"
    # Добавляем все команды из COMMANDS_LIST
    for command in COMMANDS_LIST:
        help_text += f"{command}\n"
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

@router.message(Command(commands=["goodmornigeverydayGG"]))
async def good_mornig_every_day_GG(message: types.Message):
    try:
        logging.info("Хендлер сработал!")  # Лог для подтверждения вызова

        # Получаем текущий день недели
        day_of_week = datetime.datetime.now().weekday()
        logging.info(f"Сегодня день недели: {day_of_week}")

        # Логика для дней недели
        if day_of_week == 0:  # Понедельник
            text = "Утро добрым не бывает, а понедельник ведь все-таки день тяжелый... Но не унываем!"
            file_path = os.path.join(os.getcwd(), "urls", "mond_url.txt")
        elif day_of_week in [1, 2, 3]:  # Вторник, Среда, Четверг
            text = "Всем доброго утра! Рабочий день начинается!"
            file_path = os.path.join(os.getcwd(), "urls", "workdays_url.txt")
        elif day_of_week == 4:  # Пятница
            text = "Всем доброго утра! А вот вы знали, что сегодня пятница?!"
            file_path = os.path.join(os.getcwd(), "urls", "fri_url.txt")
        elif day_of_week in [5, 6]:  # Выходные
            text = "Всем доброго утра! Выхходные! Гуляеммм!!!"
            file_path = os.path.join(os.getcwd(), "urls", "weekend_url.txt")
        else:
            logging.warning("День недели не обработан.")
            return

        # Проверка существования файла
        if not os.path.exists(file_path):
            logging.error(f"Файл {file_path} не найден.")
            await message.answer("Ошибка: файл со ссылками не найден.")
            return

        # Загрузка ссылок из файла
        with open(file_path, "r") as file:
            photo_urls = file.readlines()

        # Проверка, что список не пуст
        if not photo_urls:
            logging.error(f"Файл {file_path} пуст.")
            await message.answer("Ошибка: файл со ссылками пуст.")
            return

        # Выбор случайной ссылки
        photo_url = random.choice(photo_urls).strip()
        logging.info(f"Выбрана ссылка: {photo_url}")

        # Отправка текста и фото
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=text,
            parse_mode="Markdown"
        )
        logging.info("Сообщение отправлено успешно.")

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /goodmornigeverydayGG: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
