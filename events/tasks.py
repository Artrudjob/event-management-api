from celery import shared_task
from events.services import EventService

@shared_task
def publish_draft_events():
    EventService().publish_draft_events()
