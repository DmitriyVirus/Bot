import logging
from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from tgbot.views import join_message, left_message
from tgbot.triggers import TRIGGERS
from tgbot import views

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

@router.message()
async def debug_handler(message: Message):
    logger.info(f"Debugging update: {message}")

# Обработчик для присоединения пользователя
@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    user_name = event.new_chat_member.user.first_name
    chat_id = event.chat.id
    logging.info(f"User joined: {user_name} in chat: {chat_id}")
    
    try:
        # Отправка приветственного сообщения
        welcome_message = f"Привет, {user_name}! Добро пожаловать в чат!"
        await event.bot.send_message(chat_id, welcome_message)
        logging.info(f"Welcome message sent to {user_name} in chat {chat_id}")
    except Exception as e:
        logging.error(f"Error while sending welcome message to chat {chat_id}: {e}")

@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated):
    user_name = event.old_chat_member.user.first_name
    chat_id = event.chat.id
    logging.info(f"User left: {user_name} from chat: {chat_id}")
    
    try:
        # Отправка прощального сообщения
        goodbye_message = f"Пока, {user_name}. Надеемся, ты вернешься!"
        await event.bot.send_message(chat_id, goodbye_message)
        logging.info(f"Goodbye message sent to {user_name} in chat {chat_id}")
    except Exception as e:
        logging.error(f"Error while sending goodbye message to chat {chat_id}: {e}")
        
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
