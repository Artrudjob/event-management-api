import pytest
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone
from events.models import Event
from events.services import EventService

@pytest.mark.django_db
class TestPublishDraftEvents:
    """Ожидается, что мероприятие публикуется только после наступления даты публикации."""

    def test_change_status_after_publication(self, draft_event):
        draft_event.publication_at = timezone.now() - timedelta(minutes=1)
        draft_event.save(update_fields=["publication_at"])

        published_ids = EventService().publish_draft_events()
        draft_event.refresh_from_db()

        assert draft_event.pk in published_ids
        assert draft_event.status == Event.Status.PUBLISHED

    def test_keep_status_before_publication(self, draft_event):
        published_ids = EventService().publish_draft_events()
        draft_event.refresh_from_db()

        assert published_ids == []
        assert draft_event.status == Event.Status.DRAFT

@pytest.mark.django_db
class TestEventPublicationEmail:
    """Ожидается, что при уведомлении о публикации уходит письмо с настройками из settings."""

    @patch("events.services.event_service.send_mail")
    def test_send_notification(
        self,
        mock_send_mail,
        published_event,
        settings,
    ):
        settings.EVENT_NOTIFICATION_RECIPIENTS = ["notify@test.com"]
        settings.EVENT_NOTIFICATION_SUBJECT = "Тема публикации"
        settings.EVENT_NOTIFICATION_TEXT = "Текст публикации"

        EventService().send_notification(published_event.pk)

        mock_send_mail.assert_called_once()
        kwargs = mock_send_mail.call_args.kwargs
        assert kwargs["subject"] == "Тема публикации"
        assert kwargs["message"] == f"Текст публикации - {published_event.name}"
        assert kwargs["recipient_list"] == ["notify@test.com"]
