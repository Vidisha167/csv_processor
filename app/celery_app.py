import os

from celery import Celery

celery_app = Celery(
    "csv_processor",
    broker=os.environ["CELERY_BROKER_URL"],
    include=["app.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,              # re-queue the job if a worker dies mid-task
    worker_prefetch_multiplier=1,     # each worker takes one job at a time
    broker_connection_retry_on_startup=True,
)