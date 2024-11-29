import logging
from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from tgbot.views import join_message, left_message
from tgbot.triggers import TRIGGERS
from tgbot import views

router = Router()

# Обработчик изменения статуса участников (приход и уход)
# Обработчик для нового участника
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    logging.info(f"Received chat_member update (user joined): {event}")
    if event.new_chat_member and event.new_chat_member.status == "member":
        user = event.new_chat_member.user
        message = views.join_message(user.first_name)  # Генерируем сообщение с помощью функции join_message
        await event.bot.send_message(event.chat.id, message)

# Обработчик для ушедшего участника
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_left(event: ChatMemberUpdated):
    logging.info(f"Received chat_member update (user left): {event}")
    if event.old_chat_member and event.old_chat_member.status == "member":
        user = event.old_chat_member.user
        message = views.left_message(user.first_name)  # Генерируем сообщение с помощью функции left_message
        await event.bot.send_message(event.chat.id, message)
        
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
