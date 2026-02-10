import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.triggers import ABOUT
from tgbot.sheets.gspread_client import get_gspread_client
from tgbot.handlers.kto import fetch_data_from_sheet  # для участников чата

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


def get_hello_text() -> str:
    return get_info_column("B2:B29")


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


def format_commands(commands):
    return "\n".join(commands)


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
    hello_text = get_hello_text()
    await message.answer(
        hello_text,
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


@router.callback_query(lambda c: c.data == "menu_commands")
async def commands(callback: types.CallbackQuery):
    bot_cmds = format_commands(get_bot_commands())
    await callback.message.edit_text(bot_cmds, reply_markup=create_back_menu())


@router.callback_query(lambda c: c.data == "menu_about_bot")
async def about_bot(callback: types.CallbackQuery):
    await callback.message.edit_text(ABOUT, reply_markup=create_back_menu())


@router.callback_query(lambda c: c.data == "back_to_main")
async def back(callback: types.CallbackQuery):
    hello_text = get_hello_text()
    await callback.message.edit_text(
        hello_text,
        reply_markup=create_main_menu()
    )
