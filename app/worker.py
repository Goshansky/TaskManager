from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(
    "task_manager",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

celery.conf.task_queue_max_priority = 10
celery.conf.task_default_priority = 5

if __name__ == "__main__":
    celery.start()
