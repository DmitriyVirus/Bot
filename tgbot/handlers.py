from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from tgbot.views import join_message, left_message
from tgbot.triggers import TRIGGERS


router = Router()

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    if event.new_chat_member.user and event.new_chat_member.user.first_name:
        await event.answer(join_message(event.new_chat_member.user.first_name))
    else:
        print("Ошибка: Имя нового участника не определено.")

@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_left(event: ChatMemberUpdated):
    if event.old_chat_member.user and event.old_chat_member.user.first_name:
        await event.answer(left_message(event.old_chat_member.user.first_name))
    else:
        print("Ошибка: Имя покинувшего участника не определено.")
        
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
            
@router.message(lambda message: any(trigger in message.text for trigger in TRIGGERS))
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
