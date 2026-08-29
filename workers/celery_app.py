"""Celery worker application for CodeSentinel background scan jobs."""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "codesentinel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.tasks.scan_tasks",
        "workers.tasks.validation_tasks",
    ],
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
    task_routes={
        "workers.tasks.scan_tasks.*": {"queue": "scans"},
        "workers.tasks.validation_tasks.*": {"queue": "validations"},
    },
    task_time_limit=settings.SCAN_TIMEOUT_SECONDS + 60,
    task_soft_time_limit=settings.SCAN_TIMEOUT_SECONDS,
)
