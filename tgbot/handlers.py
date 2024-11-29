from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter
from tgbot.views import join_message, left_message
from tgbot.triggers import TRIGGERS


router = Router()

# Обработчик для нового участника
@router.chat_member(ChatMemberUpdatedFilter)
async def new_member_handler(event: ChatMemberUpdated):
    # Проверяем, что это событие связано с присоединением нового участника
    new_member = event.new_chat_member
    old_member = event.old_chat_member

    # Проверяем, что новый участник не был в группе ранее и только что присоединился
    if new_member.status == "member" and old_member.status == "left":
        new_user = new_member.user
        welcome_text = f"Привет, {new_user.full_name}! Добро пожаловать в наш чат!"
        await event.bot.send_message(event.chat.id, welcome_text)

    # Также можно добавить проверку для событий выхода из чата, если нужно
    if new_member.status == "left" and old_member.status == "member":
        left_user = old_member.user
        farewell_text = f"Прощай, {left_user.full_name}! Надеемся увидеть тебя снова!"
        await event.bot.send_message(event.chat.id, farewell_text)

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
