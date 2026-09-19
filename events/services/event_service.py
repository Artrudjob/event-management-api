from itertools import batched
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from events.models import Event

class EventService:
    CHUNK_SIZE = 100

    def send_notification(self, event_id: int) -> None:
        event = Event.objects.get(pk=event_id)
        recipients = settings.EVENT_NOTIFICATION_RECIPIENTS

        if recipients:
            self._send_notification_email(event, recipients)

    def send_notifications(self, event_ids: list[int]) -> None:
        events = Event.objects.filter(pk__in=event_ids)
        recipients = settings.EVENT_NOTIFICATION_RECIPIENTS

        if recipients:
            for event in events:
                self._send_notification_email(event, recipients)

    def _send_notification_email(
            self,
            event: Event,
            recipients: list[str]
    ) -> None:
        send_mail(
            subject=settings.EVENT_NOTIFICATION_SUBJECT,
            message=f"{settings.EVENT_NOTIFICATION_TEXT} - {event.name}",
            from_email=None,
            recipient_list=recipients,
        )

    def publish_draft_events(self) -> list[int]:
        now = timezone.now()
        published_ids = []

        event_ids = (
            Event.objects.filter(
                status=Event.Status.DRAFT,
                publication_at__lte=now,
            )
            .values_list("pk", flat=True)
            .iterator(chunk_size=self.CHUNK_SIZE)
        )

        for batch in batched(event_ids, self.CHUNK_SIZE):
            Event.objects.filter(pk__in=batch).update(
                status=Event.Status.PUBLISHED,
                update_time=now,
            )
            published_ids.extend(batch)

        return published_ids
