from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

router = Router()

# Обработчик команды /bot
@router.message(Command(commands=["bot"]))
async def bot_command_handler(message: types.Message):
    keyboard = create_main_menu()
    await message.answer("Привет, я ваш бот!", reply_markup=keyboard)

# Функция для создания главного меню
def create_main_menu():
    commands_button = InlineKeyboardButton(text="Команды", callback_data="menu_commands")
    participants_button = InlineKeyboardButton(text="Участники", callback_data="menu_participants")
    about_game_button = InlineKeyboardButton(text="Об игре", callback_data="menu_about_game")
    about_bot_button = InlineKeyboardButton(text="О боте", callback_data="menu_about_bot")
    return InlineKeyboardMarkup(inline_keyboard=[[commands_button], [participants_button], [about_game_button], [about_bot_button]])

# Функция для создания подменю "Команды"
def create_commands_menu():
    main_commands_button = InlineKeyboardButton(text="Основные", callback_data="commands_main")
    debug_commands_button = InlineKeyboardButton(text="Отладка", callback_data="commands_debug")
    back_button = InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    return InlineKeyboardMarkup(inline_keyboard=[[main_commands_button], [debug_commands_button], [back_button]])

# Обработчик для кнопок меню
@router.callback_query(lambda callback: callback.data.startswith("menu_"))
async def menu_callback_handler(callback: types.CallbackQuery):
    data = callback.data

    if data == "menu_commands":
        keyboard = create_commands_menu()
        await callback.message.edit_text("Типы команд:", reply_markup=keyboard)
    elif data == "menu_participants":
        await callback.answer("Список участников: Дмитрий, Леонид.")
    elif data == "menu_about_game":
        await callback.answer("Об игре: Игра представляет собой приключение в мире фэнтези.")
    elif data == "menu_about_bot":
        await callback.answer("О боте: Я создан для помощи в организации ваших приключений!")

# Обработчик для кнопок подменю "Команды"
@router.callback_query(lambda callback: callback.data.startswith("commands_"))
async def commands_callback_handler(callback: types.CallbackQuery):
    data = callback.data

    if data == "commands_main":
        await callback.answer("Основные команды: /start, /help, /inst.")
    elif data == "commands_debug":
        await callback.answer("Команды для отладки: /debug_info, /reset.")
    elif data == "back_to_main":
        keyboard = create_main_menu()
        await callback.message.edit_text("Привет, я ваш бот!", reply_markup=keyboard)
