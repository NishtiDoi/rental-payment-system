from celery import Celery
from app.config import settings

# Create a Celery application instance
# "rental_payment" is the name of the Celery app
# broker: Redis URL used to send tasks to the queue
# backend: Redis URL used to store task results
# Celery doesn't talk to FastAPI directly. They communicate through Redis (a super-fast data store).
celery_app = Celery(
    "rental_payment",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.payment_tasks"]
)

# Configure Celery behavior
celery_app.conf.update(
    # Serialize tasks as JSON before sending to broker
    task_serializer='json',

    # Only accept JSON content (security best practice)
    accept_content=['json'],

    # Store task results in JSON format
    result_serializer='json',

    # Set timezone for task scheduling and timestamps
    timezone='UTC',

    # Enable UTC time handling (recommended for distributed systems)
    enable_utc=True,
)
celery_app.autodiscover_tasks(["app.tasks"])