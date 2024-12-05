import logging
from aiogram import Router, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

router = Router()

# ID закрепленного сообщения (замените на нужный ID)
PINNED_MESSAGE_ID = 123456789  # Предварительно установите ID сообщения

# Обработчик команды /getidall
@router.message(Command("getidall"))
async def send_welcome(message: types.Message):
    """Приветственное сообщение."""
    await message.reply("Я собираю ID участников чата и добавляю их в сообщение!")

# Функция для извлечения участников из текста сообщения
def parse_participants(message_text: str):
    """Извлекает участников (имена и ID) из текста закрепленного сообщения."""
    participants = []
    if "Участники:" in message_text:
        lines = message_text.split("\n")
        for line in lines:
            if line.startswith("- "):  # Формат строки участника: "- Имя, ID"
                try:
                    name, user_id = line[2:].split(", ")
                    participants.append((name.strip(), user_id.strip()))
                except ValueError:
                    continue
    return participants

# Функция для обновления текста закрепленного сообщения
def generate_updated_text(original_text: str, participants: list):
    """Обновляет текст закрепленного сообщения с добавлением новых участников."""
    updated_text = original_text.split("Участники:")[0].strip()
    updated_text += "\n\nУчастники:\n" + "\n".join([f"- {name}, {user_id}" for name, user_id in participants])
    return updated_text

# Обработчик любых сообщений
@router.message()
async def collect_user_data(message: types.Message):
    """Собирает данные об участниках и обновляет сообщение."""
    bot = message.bot  # Получаем объект бота из контекста сообщения
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    chat_id = message.chat.id

    try:
        # Получаем информацию о чате
        chat = await bot.get_chat(chat_id)
        pinned_message = chat.pinned_message

        # Проверяем, есть ли закрепленное сообщение
        if pinned_message and pinned_message.message_id == PINNED_MESSAGE_ID:
            pinned_message_text = pinned_message.text

            # Извлекаем текущих участников
            current_participants = parse_participants(pinned_message_text)

            # Проверяем, есть ли пользователь уже в списке
            if (first_name, user_id) not in current_participants:
                current_participants.append((first_name, user_id))  # Добавляем нового участника

                # Генерируем обновленный текст
                updated_text = generate_updated_text(pinned_message_text, current_participants)

                # Обновляем закрепленное сообщение
                await bot.edit_message_text(
                    updated_text,
                    chat_id=chat_id,
                    message_id=PINNED_MESSAGE_ID
                )

        else:
            # Если закрепленного сообщения нет, создаем новое
            text = (
                "id участников чата:\n\nУчастники:\n"
                f"- {first_name}, {user_id}"
            )
            sent_message = await bot.send_message(chat_id, text, parse_mode="Markdown")
            await bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)
            PINNED_MESSAGE_ID = sent_message.message_id  # Сохраняем ID нового закрепленного сообщения

    except Exception as e:
        logging.error(f"Ошибка: {e}")
