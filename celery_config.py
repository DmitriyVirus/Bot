from celery import Celery
from decouple import config

# Получаем Redis URL из переменных окружения
redis_url = config('REDIS_URL')  # URL Redis на Render

# Настройка Celery с использованием Redis
celery_app = Celery(
    "tgbot",  # Имя приложения
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.update(
    result_expires=3600,  # Время хранения результатов задач
)
