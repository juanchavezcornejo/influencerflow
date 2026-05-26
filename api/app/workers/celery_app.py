"""Celery application.

Worker entrypoint:
    celery -A app.workers.celery_app worker --loglevel=info --queues=default
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "influencerflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks_sync",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    task_track_started=True,
    # Sensible retry defaults; per-task overrides are still respected.
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)
