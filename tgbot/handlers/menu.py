import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.triggers import (
    ABOUT, ABOUT_GAME, DAREDEVILS,
    COMMANDS_LIST, DEBUG_BOT, TRIGGERS,
    DETRON, MACROS
)
from tgbot.sheets.gspread_client import get_gspread_client
from tgbot.handlers.kto import fetch_data_from_sheet  # импорт вынесен сюда

router = Router()
logger = logging.getLogger(__name__)

ADMINS = {1141764502, 559273200}
EXCLUDED_USER_IDS = {559273200}


# ===== ЧТЕНИЕ ДАННЫХ ИЗ GOOGLE SHEETS =====

def get_info_column(range_name: str) -> str:
    client = get_gspread_client()
    if not client:
        return "Данные недоступны"

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
        values = sheet.get(range_name)
    except Exception as e:
        logger.error(f"Ошибка чтения диапазона {range_name}: {e}")
        return "Данные недоступны"

    if not values:
        return "Данные недоступны"

    return "\n".join(row[0] for row in values if row and row[0])


def get_bot_commands() -> list[str]:
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
        rows = sheet.get("C2:D")
    except Exception as e:
        logger.error(f"Ошибка чтения команд бота: {e}")
        return ["Команды недоступны"]

    commands = []
    for row in rows:
        cmd = row[0].strip() if len(row) > 0 else ""
        text = row[1].strip() if len(row) > 1 else ""
        if not cmd:
            continue
        commands.append(f"{cmd} — {text}" if text else cmd)

    return commands


def get_bot_deb_cmd() -> list[str]:
    client = get_gspread_client()
    if not client:
        return ["Команды недоступны"]

    try:
        sheet = client.open("DareDevils").worksheet("Инфо")
        rows = sheet.get("E2:F")
    except Exception as e:
        logger.error(f"Ошибка чтения debug-команд: {e}")
        return ["Команды недоступны"]

    commands = []
    for row in rows:
        cmd = row[0].strip() if len(row) > 0 else ""
        text = row[1].strip() if len(row) > 1 else ""
        if not cmd:
            continue
        commands.append(f"{cmd} — {text}" if text else cmd)

    return commands


# ===== ЛЕНИВЫЕ ДОСТУПЫ К ДАННЫМ =====

def get_welcome_text() -> str:
    return get_info_column("A2:A29")

def get_hello_text() -> str:
    return get_info_column("B2:B29")

def get_bot_cmd_text() -> str:
    return format_commands(get_bot_commands())

def get_bot_deb_cmd_text() -> str:
    return format_commands(get_bot_deb_cmd())


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_excluded_user(user_id: int) -> bool:
    return user_id in EXCLUDED_USER_IDS

def format_commands(commands):
    return "\n".join(commands)

def format_triggers(triggers):
    return "\n".join([f"{i + 1}. {t}" for i, t in enumerate(triggers.keys())])


# ===== КЛАВИАТУРЫ =====

def create_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😈 DareDevils", callback_data="menu_daredevils")],
        [InlineKeyboardButton(text="👽 Участники чата", callback_data="menu_participants")],
        [InlineKeyboardButton(text="ℹ️ Информация об игре", callback_data="menu_about_game")],
        [InlineKeyboardButton(text="🤖 Команды для бота", callback_data="menu_commands")],
        [InlineKeyboardButton(text="⚙️ Информация о боте", callback_data="menu_about_bot")]
    ])

def create_back_menu(back="back_to_main"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏃 Назад", callback_data=back)]]
    )

def create_game_info_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💢 Свержение", callback_data="menu_revolution")],
        [InlineKeyboardButton(text="🔯 Макросы", callback_data="menu_macros")],
        [InlineKeyboardButton(text="🏃 Назад", callback_data="back_to_main")]
    ])

def create_commands_menu(is_admin_user: bool):
    keyboard = [[InlineKeyboardButton(text="Основные", callback_data="commands_main")]]
    if is_admin_user:
        keyboard.append([InlineKeyboardButton(text="Отладка", callback_data="commands_debug")])
    keyboard.append([InlineKeyboardButton(text="🏃 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ===== ХЕНДЛЕРЫ =====

@router.message(Command("bot"))
async def bot_menu(message: types.Message):
    await message.answer(
        get_hello_text(),
        reply_markup=create_main_menu(),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == "menu_daredevils")
async def daredevils(callback: types.CallbackQuery):
    await callback.message.edit_text(
        DAREDEVILS,
        reply_markup=create_back_menu(),
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "menu_about_bot")
async def about_bot(callback: types.CallbackQuery):
    await callback.message.edit_text(
        ABOUT,
        reply_markup=create_back_menu(),
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "menu_commands")
async def commands(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if is_excluded_user(user_id):
        await callback.message.edit_text(
            "Типы команд:",
            reply_markup=create_commands_menu(is_admin(user_id))
        )
        return

    await callback.message.edit_text(
        f"Команды:\n{get_bot_cmd_text()}",
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "commands_main")
async def main_commands(callback: types.CallbackQuery):
    await callback.message.edit_text(
        get_bot_cmd_text(),
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "commands_debug")
async def debug_commands(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        get_bot_deb_cmd_text(),
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "menu_participants")
async def participants(callback: types.CallbackQuery):
    """
    Выводит всех участников из Google Sheets через fetch_data_from_sheet
    """
    client = get_gspread_client()
    if not client:
        await callback.message.edit_text("Ошибка подключения к Google Sheets.")
        return

    expanded_table = fetch_data_from_sheet(client)
    if not expanded_table:
        await callback.message.edit_text("Данные недоступны.")
        return

    response = "Список всех пользователей:\n"
    for user_name, user_info in expanded_table.items():
        if user_name == user_info["name"].lower():  # уникальные записи
            response += (
                f"\nИмя: {user_info['name']}\n"
                f"{f'Имя в телеграмм: {user_info['tgnick']}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                f"{f'Ник: @{user_info['nick']}\n' if user_info['nick'] != 'Unknown' else ''}"
                f"Инфо: {user_info['about']}\n"
            )

    await callback.message.edit_text(response, reply_markup=create_back_menu())


@router.callback_query(lambda c: c.data in {"back_to_main", "menu_about_game"})
async def back(callback: types.CallbackQuery):
    if callback.data == "menu_about_game":
        await callback.message.edit_text(
            ABOUT_GAME,
            reply_markup=create_game_info_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            get_hello_text(),
            reply_markup=create_main_menu()
        )


@router.callback_query(lambda c: c.data == "menu_revolution")
async def revolution(callback: types.CallbackQuery):
    await callback.message.edit_text(
        DETRON,
        reply_markup=create_back_menu("menu_about_game"),
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "menu_macros")
async def macros(callback: types.CallbackQuery):
    await callback.message.edit_text(
        MACROS,
        reply_markup=create_back_menu("menu_about_game"),
        parse_mode="HTML"
    )
