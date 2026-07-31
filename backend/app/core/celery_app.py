from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "autodocops",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_default_queue="default",
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "pipeline": {"exchange": "pipeline", "routing_key": "pipeline"},
        "analysis": {"exchange": "analysis", "routing_key": "analysis"},
    },
    task_routes={
        "app.workers.tasks.run_push_pipeline": {"queue": "pipeline"},
        "app.workers.tasks.run_pr_analysis": {"queue": "analysis"},
    },
    beat_schedule={},
)
