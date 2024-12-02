from celery import Celery
from decouple import config  # Для работы с переменными окружения

# Читаем URL Redis из переменной окружения
redis_url = config("REDIS_URL")  # REDIS_URL должен быть задан в Environment Variables

# Проверяем, что REDIS_URL корректно загружен
if not redis_url:
    raise ValueError("Переменная окружения REDIS_URL не задана или пустая.")

# Создаем экземпляр Celery с Redis в качестве брокера и backend
celery_app = Celery(
    "tgbot",
    broker=redis_url,
    backend=redis_url,
)

# Настройка Celery
celery_app.conf.update(
    result_expires=3600,  # Результаты задач хранятся 1 час
)
