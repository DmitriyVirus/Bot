from celery import Celery
from upstash_redis import Redis

# Настройка Redis для Upstash
redis = Redis(url="https://gusc1-striking-platypus-30618.upstash.io", token="AXeaASQgYjdkNWNjOTktMDU3ZS00YzBkLWE2ZGEtNWFkNTg5ZmNlN2M3OWU4ZWE3NTY2NWJkNGVjOWExNTFmZTYyNWQ4NWQxNjg=")

# Инициализация Celery с использованием Redis как брокера
celery_app = Celery(
    "tgbot",
    broker=f"redis://{redis.client.host}:{redis.client.port}/{redis.client.db}",
    backend=f"redis://{redis.client.host}:{redis.client.port}/{redis.client.db}",
)

celery_app.conf.update(
    result_expires=3600,  # Время хранения результатов задач в секундах
)
