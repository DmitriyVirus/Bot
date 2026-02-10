import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.sheets.gspread_client import get_gspread_client
from tgbot.handlers.kto import fetch_data_from_sheet  # Импорт для участников чата

router = Router()
logger = logging.getLogger(__name__)

ADMINS = {1141764502, 559273200}
EXCLUDED_USER_IDS = {559273200}


# ===== ЧТЕНИЕ ДАННЫХ ИЗ GOOGLE SHEETS =====

def get_info_column_by_header(header_name: str) -> str:
    """
    Читает колонку по имени заголовка (header_name) в листе 'Инфо'
    и возвращает текст, склеенный через перенос строки.
    """
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
        headers = sheet.row_values(1)
        if header_name not in headers:
            return f"Колонка '{header_name}' не найдена"
        col_index = headers.index(header_name) + 1  # gspread использует 1-based индексы
        values = sheet.col_values(col_index)[1:]  # пропускаем заголовок
    except Exception as e:
        logger.error(f"Ошибка чтения колонки '{header_name}': {e}")
        return "Данные недоступны"

    if not values:
        return "Данные недоступны"

    return "\n".join(row for row in values if row)


def get_bot_commands() -> list[str]:
    """
    Читает основные команды бота (cmd_bot + cmd_bot_text)
    """
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
        headers = sheet.row_values(1)
        c_index = headers.index("cmd_bot") + 1
        d_index = headers.index("cmd_bot_text") + 1
        cmd_values = sheet.col_values(c_index)[1:]
        text_values = sheet.col_values(d_index)[1:]
    except Exception as e:
        logger.error(f"Ошибка чтения команд бота: {e}")
        return ["Команды недоступны"]

    commands = []
    for cmd, text in zip(cmd_values, text_values):
        cmd = cmd.strip() if cmd else ""
        text = text.strip() if text else ""
        if not cmd:
            continue
        commands.append(f"{cmd} — {text}" if text else cmd)
    return commands


def get_bot_deb_cmd() -> list[str]:
    """
    Читает команды отладки бота (cmd_bot_deb + cmd_bot_deb_text)
    """
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
        headers = sheet.row_values(1)
        c_index = headers.index("cmd_bot_deb") + 1
        d_index = headers.index("cmd_bot_deb_text") + 1
        cmd_values = sheet.col_values(c_index)[1:]
        text_values = sheet.col_values(d_index)[1:]
    except Exception as e:
        logger.error(f"Ошибка чтения debug-команд: {e}")
        return ["Команды недоступны"]

    commands = []
    for cmd, text in zip(cmd_values, text_values):
        cmd = cmd.strip() if cmd else ""
        text = text.strip() if text else ""
        if not cmd:
            continue
        commands.append(f"{cmd} — {text}" if text else cmd)
    return commands


# ===== ЛЕНИВЫЕ ДОСТУПЫ К ДАННЫМ =====

def get_welcome_text() -> str:
    return get_info_column_by_header("Welcome")

def get_hello_text() -> str:
    return get_info_column_by_header("Hello")

def get_about_bot_text() -> str:
    return get_info_column_by_header("about_bot")

def get_bot_cmd_text() -> str:
    return "\n".join(get_bot_commands())

def get_bot_deb_cmd_text() -> str:
    return "\n".join(get_bot_deb_cmd())


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_excluded_user(user_id: int) -> bool:
    return user_id in EXCLUDED_USER_IDS


# ===== КЛАВИАТУРЫ =====

def create_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👽 Участники чата", callback_data="menu_participants")],
        [InlineKeyboardButton(text="🤖 Команды для бота", callback_data="menu_commands")],
        [InlineKeyboardButton(text="⚙️ Информация о боте", callback_data="menu_about_bot")]
    ])

def create_back_menu(back="back_to_main"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏃 Назад", callback_data=back)]]
    )


# ===== ХЕНДЛЕРЫ =====

@router.message(Command("bot"))
async def bot_menu(message: types.Message):
    text = f"{get_hello_text()}\n\n{get_about_bot_text()}"
    await message.answer(
        text,
        reply_markup=create_main_menu(),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == "menu_participants")
async def participants(callback: types.CallbackQuery):
    client = get_gspread_client()
    if not client:
        await callback.message.edit_text("Ошибка подключения к Google Sheets.")
        return

    expanded_table = fetch_data_from_sheet(client)
    if not expanded_table:
        await callback.message.edit_text("Ошибка загрузки данных из Google Sheets.")
        return

    response = "Список всех участников:\n"
    for user_name, user_info in expanded_table.items():
        if user_name == user_info["name"].lower():  # уникальные записи
            response += (
                f"\nИмя: {user_info['name']}\n"
                f"{f'Имя в телеграмм: {user_info['tgnick']}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                f"{f'Ник: @{user_info['nick']}\n' if user_info['nick'] != 'Unknown' else ''}"
                f"Инфо: {user_info['about']}\n"
            )

    await callback.message.edit_text(
        response,
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "menu_commands")
async def commands(callback: types.CallbackQuery):
    await callback.message.edit_text(
        get_bot_cmd_text(),
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "menu_about_bot")
async def about_bot(callback: types.CallbackQuery):
    await callback.message.edit_text(
        get_about_bot_text(),
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "back_to_main")
async def back(callback: types.CallbackQuery):
    text = f"{get_hello_text()}\n\n{get_about_bot_text()}"
    await callback.message.edit_text(
        text,
        reply_markup=create_main_menu()
    )
