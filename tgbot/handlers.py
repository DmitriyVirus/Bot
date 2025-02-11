import os  
import random  
import logging
import datetime 
from config import config 
from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import Message, User, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.triggers import TRIGGERS, WELCOME_TEXT, COMMANDS_LIST, FIRST, ABOUT, DEBUG_BOT, DAREDEVILS, ABOUT_GAME, DETRON, MACROS
from tgbot.gspread_client import get_gspread_client
from tgbot.google_sheets import fetch_data_from_sheet

# Использование клиента
client = get_gspread_client()
if client:
    sheet = client.open("ourid").sheet1

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
        [InlineKeyboardButton(text="😈DareDevils", callback_data="menu_daredevils")],
        [InlineKeyboardButton(text="👽Участники чата", callback_data="menu_participants")],
        [InlineKeyboardButton(text="ℹ️Информация об игре", callback_data="menu_about_game")],
        [InlineKeyboardButton(text="🤖Команды для бота", callback_data="menu_commands")],
        [InlineKeyboardButton(text="⚙️Информация о боте", callback_data="menu_about_bot")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция для создания меню с дополнительными кнопками
def create_game_info_menu():
    buttons = [
        [InlineKeyboardButton(text="💢Свержение", callback_data="menu_revolution")],
        [InlineKeyboardButton(text="🔯Макросы", callback_data="menu_macros")],
        [InlineKeyboardButton(text="🏃Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция для создания подменю с одной кнопкой "Назад"
def create_back_menu(back_callback: str = "back_to_main"):
    """Создает меню с одной кнопкой 'Назад', указывающей на заданный callback."""
    back_button = InlineKeyboardButton(text="🏃Назад", callback_data=back_callback)
    return InlineKeyboardMarkup(inline_keyboard=[[back_button]])

# Функция для создания меню команд
def create_commands_menu(is_admin_user: bool):
    main_commands_button = InlineKeyboardButton(text="Основные", callback_data="commands_main")
    back_button = InlineKeyboardButton(text="🏃Назад", callback_data="back_to_main")
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
        parse_mode="Markdown",  # Используем MarkdownV2 для правильного форматирования
    )

# Обработчик для кнопки "DareDevils"
@router.callback_query(lambda callback: callback.data == "menu_daredevils")
async def menu_daredevils_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        DAREDEVILS,
        reply_markup=create_back_menu(),
        parse_mode="HTML",
        disable_web_page_preview=True  # Отключаем предпросмотр ссылок
    )
    
# Обработчик для кнопки "Участники"
@router.callback_query(lambda callback: callback.data == "menu_participants")
async def menu_participants_handler(callback: types.CallbackQuery):
    client = get_gspread_client()
    if not client:
        await callback.message.edit_text("Ошибка подключения к Google Sheets.")
        return

    # Загружаем данные из Google Sheets
    expanded_table = fetch_data_from_sheet(client)
    if not expanded_table:
        await callback.message.edit_text("Ошибка загрузки данных из Google Sheets.")
        return

    response = "Список всех пользователей:\n"
    
    # Формируем строку с данными пользователей
    for user_name, user_info in expanded_table.items():
        if user_name == user_info["name"].lower():  # Уникальные записи
            response += (
                f"\nИмя: {user_info['name']}\n"
                f"{f'Имя в телеграмм: {user_info['tgnick']}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                f"{f'Ник: @{user_info['nick']}\n' if user_info['nick'] != 'Unknown' else ''}"
                f"Инфо: {user_info['about']}\n"
            )

    # Ограничение на длину сообщения
    MAX_MESSAGE_LENGTH = 4096
    
    # Если сообщение слишком длинное, разделим его на части
    if len(response) > MAX_MESSAGE_LENGTH:
        for i in range(0, len(response), MAX_MESSAGE_LENGTH):
            await callback.message.edit_text(response[i:i + MAX_MESSAGE_LENGTH], reply_markup=create_back_menu())
    else:
        # Отправляем сообщение целиком
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

# Обработчик для кнопки "Назад"
@router.callback_query(lambda callback: callback.data in {"back_to_main", "menu_about_game"})
async def back_to_main_handler(callback: types.CallbackQuery):
    if callback.data == "menu_about_game":
        keyboard = create_game_info_menu()
        await callback.message.edit_text(
            ABOUT_GAME,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        keyboard = create_main_menu()
        await callback.message.edit_text(FIRST, reply_markup=keyboard)

# Обработчик для кнопки "Информация об игре"
@router.callback_query(lambda callback: callback.data == "menu_about_game")
async def menu_about_game_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        ABOUT_GAME,
        reply_markup=create_game_info_menu(),
        parse_mode="HTML",
        disable_web_page_preview=True  # Отключаем предпросмотр ссылок
    )

# Обработчик для кнопки "Свержение"
@router.callback_query(lambda callback: callback.data == "menu_revolution")
async def menu_revolution_handler(callback: types.CallbackQuery):
    # Отправляем текст о Свержении и кнопку "Назад" к меню "Информация об игре"
    await callback.message.edit_text(
        DETRON,
        reply_markup=create_back_menu(back_callback="menu_about_game"),
        parse_mode="HTML",  # Используем Markdown для форматирования
        disable_web_page_preview=True  # Отключаем предпросмотр ссылок
    )

# Обработчик для кнопки "Макросы"
@router.callback_query(lambda callback: callback.data == "menu_macros")
async def menu_macros_handler(callback: types.CallbackQuery):
    # Отправляем текст о Макросах и кнопку "Назад" к меню "Информация об игре"
    await callback.message.edit_text(
        MACROS,
        reply_markup=create_back_menu(back_callback="menu_about_game"),
        parse_mode="HTML",  # Используем Markdown для форматирования
        disable_web_page_preview=True  # Отключаем предпросмотр ссылок
    )
        
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
        welcome_text = f"⚡⚡⚡Привет, *{new_member.first_name}*! Теперь ты часть команды.⚡⚡⚡ {WELCOME_TEXT}\n\nЯ Бот клана DaraDevils и если ты хочешь узнать больше информации о нас используй команду /bot."
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
async def bye1_handler(message: Message):
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
async def bye2_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIDI2dLDIjfeiMQ55Ae8yv-GzRHfSnZAAIzXAACVk5YSlsGnAdQnVQ7NgQ"  # Ваш file_id
    try:
        # Отправляем видео с использованием file_id
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")

# Обработчик команды /leo
@router.message(Command(commands=["leo"]))  # Используем фильтр Command
async def leo_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAID7Gduy9JTCQKSgMJhi5Py2oUJjUHQAAIwYAACVVt4S58U06_aKUcxNgQ"  # Ваш file_id
    try:
        # Отправляем видео с использованием file_id
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")

# Обработчик команды /leo
@router.message(Command(commands=["leo2"]))  # Используем фильтр Command
async def leo2_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIEFWeXoBlmVc80Ur6388o5KD0mcvm4AAJbcAACMke4SKrI6LtJuRAENgQ"  # Ваш file_id
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
async def klaar_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIDgWdar1ZHi4Baas954WdvLHCKOv35AAIlYAAC3ejZSvIFDXGe8drUNgQ"  # Ваш file_id
    try:
        # Отправляем видео с использованием file_id
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")

# Обработчик команды /kris
@router.message(Command(commands=["kris"]))  # Используем фильтр Command
async def kris_handler(message: Message):
    photo_url = "https://i.redd.it/xces20zltm3b1.jpg"  # Укажите URL картинки
    caption = "Спасайтесь, это Крис!"  # Подпись к изображению
    try:
        # Отправляем изображение с использованием URL и добавляем подпись
        await message.answer_photo(photo_url, caption=caption)
        print(f"Изображение отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке изображения: {e}")
        print(f"Ошибка при отправке изображения: {e}")

# Обработчик команды /gg1
@router.message(Command(commands=["gg1"]))
async def gg1_handler(message: Message):
    audio_file_id = "CQACAgIAAxkBAAIDz2dsbKGQt2QI0cekxKLevS0twoS5AAJZeQACSQJgS_3cy6cxtBIDNgQ"
    try:
        # Отправляем аудиофайл с использованием file_id
        await message.answer_audio(audio_file_id)
        print(f"Мелодия отправлена пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке аудио: {e}")
        print(f"Ошибка при отправке аудио: {e}")

# Обработчик команды /gg2
@router.message(Command(commands=["gg2"]))  # Используем фильтр Command
async def gg2_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIEFmek8eXnxDZfC7IvohKH6AP2stiOAALhaAACBmEgSWS7P8nmMeeSNgQ"  # Ваш file_id
    try:
        # Отправляем видео с использованием file_id
        await message.answer_video(video_file_id)
        print(f"Видео отправлено пользователю {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка при отправке видео: {e}")
        print(f"Ошибка при отправке видео: {e}")

# Обработчик команды /gg3
@router.message(Command(commands=["gg3"]))  # Используем фильтр Command
async def gg3_handler(message: Message):
    video_file_id = "BAACAgIAAxkBAAIEF2erbGieXUSQeN_rrhRPkcm_LbWwAAI7agAC_f9ZSfauT3j18V0sNgQ"  # Ваш file_id
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
