from celery import shared_task
from events.services import EventService

@shared_task
def publish_draft_events():
    event_ids = EventService().publish_draft_events()
    if event_ids:
        send_notifications.delay(event_ids)

@shared_task
def send_notification(event_id: int):
    EventService().send_notification(event_id)


@shared_task
def send_notifications(event_ids: list[int]):
    EventService().send_notifications(event_ids)
