from .celery_config import celery_app
import time

@celery_app.task(name="tasks.long_task")
def long_task(duration):
    time.sleep(duration)
    return f"Task completed in {duration} seconds"
