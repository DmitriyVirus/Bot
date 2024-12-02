from celery import Celery
import os

# Настройка Redis URL (например, из Railway)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Создание приложения Celery
celery_app = Celery(
    "celery_tasks",  # Название приложения
    broker=redis_url,
    backend=redis_url,
)

# Опциональные настройки Celery
celery_app.conf.update(
    result_expires=3600,  # Время жизни результатов задач
    task_serializer="json",
    accept_content=["json"],
)
