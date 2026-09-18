from itertools import batched
from django.utils import timezone
from events.models import Event

class EventService:
    CHUNK_SIZE = 100

    def publish_draft_events(self) -> int:
        now = timezone.now()
        published = 0

        event_ids = (
            Event.objects.filter(
                status=Event.Status.DRAFT,
                publication_at__lte=now,
            )
            .values_list("pk", flat=True)
            .iterator(chunk_size=self.CHUNK_SIZE)
        )

        for batch in batched(event_ids, self.CHUNK_SIZE):
            published += Event.objects.filter(pk__in=batch).update(
                status=Event.Status.PUBLISHED,
                update_time=now,
            )

        return published


