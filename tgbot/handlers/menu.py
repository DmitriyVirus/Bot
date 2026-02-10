import os
import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from tgbot.sheets.take_from_sheet import (
    get_info_column_by_header,
    get_bot_commands,
    get_bot_deb_cmd,
    fetch_participants,
    get_admins_records
)

router = Router()
logger = logging.getLogger(__name__)

WEBAPP_URL = os.environ.get("WEBAPP_URL")

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def format_commands(commands: list[str]) -> str:
    return "\n".join(commands)

def is_user_allowed(user_id: int) -> bool:
    records = get_admins_records()
    if not records:
        return False

    for record in records:
        if str(record.get("id")) == str(user_id):
            return True
    return False

# ===== КЛАВИАТУРЫ =====

def create_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👽 Участники чата", callback_data="menu_participants")],
        [InlineKeyboardButton(text="🤖 Команды для бота", callback_data="menu_commands")],
        [InlineKeyboardButton(text="ℹ️ Информация о боте", callback_data="menu_about_bot")]
    ])

def create_back_menu(back="back_to_main"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏃 Назад", callback_data=back)]]
    )

def create_about_bot_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Описание бота", callback_data="about_description")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton(text="🏃 Назад", callback_data="back_to_main")]
    ])

def create_settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Редактировать таблицу участников",
                    web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/google_tab")
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛠 Сервис",
                    callback_data="menu_service"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏃 Назад",
                    callback_data="menu_about_bot"
                )
            ]
        ]
    )

# ===== ХЭНДЛЕРЫ =====

@router.callback_query(lambda c: c.data == "menu_about_bot")
async def about_bot_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ Информация о боте",
        reply_markup=create_about_bot_menu()
    )

@router.callback_query(lambda c: c.data == "menu_settings")
async def settings_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_user_allowed(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "⚙️ Настройки",
        reply_markup=create_settings_keyboard()
    )

@router.callback_query(lambda c: c.data == "menu_service")
async def service_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_user_allowed(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    commands = get_bot_deb_cmd()
    text = format_commands(commands)

    await callback.message.edit_text(
        f"🛠 Сервисные команды:\n\n{text}",
        reply_markup=create_back_menu("menu_settings")
    )
