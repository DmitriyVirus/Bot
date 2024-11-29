from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated, ChatMember
from aiogram.filters import Command  # Импорт фильтра Command
from tgbot.triggers import TRIGGERS

router = Router()

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

@router.chat_member()
async def new_member_handler(event: ChatMemberUpdated):
    new_member = event.new_chat_member
    chat_id = event.chat.id
    
    # Проверка на тип вступления
    if new_member.status == ChatMember.NEW:
        first_name = new_member.user.first_name
        if event.old_chat_member and event.old_chat_member.inviter is None:  # Вступление по ссылке
            greeting = f"Привет, {first_name}! Ты пришел по ссылке, добро пожаловать!"
        elif event.old_chat_member:  # Вступление вручную
            greeting = f"Привет, {first_name}! Добро пожаловать, ты был приглашен вручную!"
        else:
            # Для случаев, когда приглашение неизвестно
            greeting = f"Привет, {first_name}! Добро пожаловать в наш чат!"

        try:
            await event.bot.send_message(chat_id, greeting)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")

            
@router.message(lambda message: any(trigger in message.text.lower() for trigger in TRIGGERS))
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
