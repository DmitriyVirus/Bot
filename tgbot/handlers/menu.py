import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.triggers import (
    FIRST, ABOUT, ABOUT_GAME, DAREDEVILS,
    COMMANDS_LIST, DEBUG_BOT, TRIGGERS,
    DETRON, MACROS
)
from tgbot.sheets.gspread_client import get_gspread_client

router = Router()
logger = logging.getLogger(__name__)

ADMINS = {1141764502, 559273200}
EXCLUDED_USER_IDS = {559273200}


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_excluded_user(user_id: int) -> bool:
    return user_id in EXCLUDED_USER_IDS

def format_commands(commands):
    return "\n".join(commands)

def format_triggers(triggers):
    return "\n".join([f"{i+1}. {t}" for i, t in enumerate(triggers.keys())])


# ===== КЛАВИАТУРЫ =====

def create_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😈DareDevils", callback_data="menu_daredevils")],
        [InlineKeyboardButton(text="👽Участники чата", callback_data="menu_participants")],
        [InlineKeyboardButton(text="ℹ️Информация об игре", callback_data="menu_about_game")],
        [InlineKeyboardButton(text="🤖Команды для бота", callback_data="menu_commands")],
        [InlineKeyboardButton(text="⚙️Информация о боте", callback_data="menu_about_bot")]
    ])

def create_back_menu(back="back_to_main"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏃Назад", callback_data=back)]]
    )

def create_game_info_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💢Свержение", callback_data="menu_revolution")],
        [InlineKeyboardButton(text="🔯Макросы", callback_data="menu_macros")],
        [InlineKeyboardButton(text="🏃Назад", callback_data="back_to_main")]
    ])

def create_commands_menu(is_admin_user: bool):
    keyboard = [[InlineKeyboardButton(text="Основные", callback_data="commands_main")]]
    if is_admin_user:
        keyboard.append([InlineKeyboardButton(text="Отладка", callback_data="commands_debug")])
    keyboard.append([InlineKeyboardButton(text="🏃Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ===== ХЕНДЛЕРЫ =====

@router.message(Command("bot"))
async def bot_menu(message: types.Message):
    await message.answer(FIRST, reply_markup=create_main_menu(), parse_mode="Markdown")


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
        f"Команды:\n{format_commands(COMMANDS_LIST)}\n\n"
        f"Триггеры:\n{format_triggers(TRIGGERS)}",
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "commands_debug")
async def debug_commands(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        format_commands(DEBUG_BOT),
        reply_markup=create_back_menu()
    )


@router.callback_query(lambda c: c.data == "commands_main")
async def main_commands(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"{format_commands(COMMANDS_LIST)}\n\n{format_triggers(TRIGGERS)}",
        reply_markup=create_back_menu()
    )


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
            FIRST,
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
