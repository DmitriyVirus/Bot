import logging
from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from tgbot.views import join_message, left_message
from tgbot.triggers import TRIGGERS

router = Router()

# Обработчик изменения статуса участников (приход и уход)
@router.chat_member(ChatMemberUpdatedFilter())
async def on_user_status_changed(event: ChatMemberUpdated):
    # Логируем событие
    logging.info(f"Received chat_member update: {event}")

    # Обработка прихода нового пользователя
    if event.old_chat_member.status == "left" and event.new_chat_member.status == "member":
        user = event.new_chat_member.user
        logging.info(f"User {user.full_name} joined the chat.")
        await event.bot.send_message(event.chat.id, f"Добро пожаловать, {user.full_name}!")

    # Обработка ухода пользователя
    elif event.old_chat_member.status == "member" and event.new_chat_member.status == "left":
        user = event.old_chat_member.user
        logging.info(f"User {user.full_name} left the chat.")
        await event.bot.send_message(event.chat.id, f"Прощай, {user.full_name}!")

# Обработчик команды /help
@router.message(Command(commands=["help"]))  # Используем фильтр Command
async def help_handler(message: Message):
    help_text = "*Привет, дружище! Я Бот этого чата и слежу за тобой!*\n\n" \
                "Я приветствую новичков, слежу за порядком и делаю рассылки по активностям.\n\n" \
                "Так же, я могу ответить на следующие фразы:\n"
    
    # Перебираем триггеры и нумеруем их
    for i, trigger in enumerate(TRIGGERS, 1):
        # Извлекаем часть до символа ":" или оставляем сам текст, если ":" нет
        trigger_text = trigger.split(":")[0]
        # Преобразуем первую букву в верхний регистр
        trigger_text = trigger_text.capitalize()
        help_text += f"{i}. {trigger_text}\n"  # Добавляем номер и фразу
    
    await message.answer(help_text, parse_mode="Markdown")
            
@router.message(lambda message: message.text and any(trigger in message.text.lower() for trigger in TRIGGERS))
async def trigger_handler(message: Message):
    message_text = message.text.lower()  # Преобразуем текст в нижний регистр
    for trigger, response in TRIGGERS.items():
        if trigger in message_text:
            if isinstance(response, dict):  # Если ответ это словарь (с текстом, изображением или gif)
                # Отправляем текст
                if "text" in response:
                    await message.answer(response["text"], parse_mode="Markdown")
                
                # Отправляем изображение, если есть
                if "image" in response:
                    await message.answer_photo(response["image"])
                
                # Отправляем gif, если есть
                if "gif" in response:
                    await message.answer_animation(response["gif"])
            
            else:
                await message.answer(response, parse_mode="Markdown")  # Отправляем текст
            break  # Прекращаем проверку после первого совпадения
