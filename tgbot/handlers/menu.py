import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.sheets.take_from_sheet import (
    get_info_column_by_header,
    get_bot_commands
)
from tgbot.handlers.kto import fetch_data_from_sheet  # Импорт для участников чата

router = Router()
logger = logging.getLogger(__name__)


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
    # Показываем только Hello при вызове команды /bot
    await message.answer(
        get_info_column_by_header("Hello"),
        reply_markup=create_main_menu(),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == "menu_participants")
async def participants(callback: types.CallbackQuery):
    client = get_gspread_client()
    if not client:
        await callback.message.edit_text("Ошибка подключения к Google Sheets.", reply_markup=create_back_menu())
        return

    expanded_table = fetch_data_from_sheet(client)
    if not expanded_table:
        await callback.message.edit_text("Ошибка загрузки данных из Google Sheets.", reply_markup=create_back_menu())
        return

    response = "Список всех участников:\n"
    for user_name, user_info in expanded_table.items():
        if user_name == user_info["name"].lower():
            response += (
                f"\nИмя: {user_info['name']}\n"
                f"{f'Имя в телеграмм: {user_info['tgnick']}\n' if user_info['tgnick'] != 'Unknown' else ''}"
                f"{f'Ник: @{user_info['nick']}\n' if user_info['nick'] != 'Unknown' else ''}"
                f"Инфо: {user_info['about']}\n"
            )

    await callback.message.edit_text(response, reply_markup=create_back_menu())


@router.callback_query(lambda c: c.data == "menu_commands")
async def commands(callback: types.CallbackQuery):
    # Показываем сразу основные команды
    await callback.message.edit_text(
        "\n".join(get_bot_commands()),
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "menu_about_bot")
async def about_bot(callback: types.CallbackQuery):
    await callback.message.edit_text(
        get_info_column_by_header("about_bot"),
        reply_markup=create_back_menu(),
        disable_web_page_preview=True
    )


@router.callback_query(lambda c: c.data == "back_to_main")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        get_info_column_by_header("Hello"),
        reply_markup=create_main_menu()
    )
