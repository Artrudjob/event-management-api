import pytest
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from events.models import Event, Venue

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="password",
    )

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="user",
        email="user@test.com",
        password="password",
    )

@pytest.fixture
def venue(db):
    return Venue.objects.create(
        name="Тест место",
        latitude="55.751244",
        longitude="37.618423",
    )

@pytest.fixture
def venue_payload():
    return {
        "name": "Новое тест место",
        "latitude": "59.934280",
        "longitude": "30.335100",
    }

@pytest.fixture
def superuser_client(api_client, superuser):
    api_client.force_authenticate(user=superuser)

    return api_client

@pytest.fixture
def user_client(api_client, user):
    api_client.force_authenticate(user=user)

    return api_client

@pytest.fixture
def published_event(venue, superuser):
    now = timezone.now()
    return Event.objects.create(
        name="Опубликованное мероприятие",
        publication_at=now - timedelta(days=1),
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=2),
        venue=venue,
        rating=10,
        status=Event.Status.PUBLISHED,
        author=superuser,
    )

@pytest.fixture
def draft_event(venue, superuser):
    now = timezone.now()
    return Event.objects.create(
        name="Черновик мероприятия",
        publication_at=now + timedelta(days=7),
        starts_at=now + timedelta(days=8),
        ends_at=now + timedelta(days=9),
        venue=venue,
        rating=5,
        status=Event.Status.DRAFT,
        author=superuser,
    )

@pytest.fixture
def event_payload(venue):
    now = timezone.now()
    return {
        "name": "Новое мероприятие",
        "description": "Описание",
        "publication_at": (now - timedelta(hours=1)).isoformat(),
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=2)).isoformat(),
        "venue": venue.pk,
        "rating": 8,
    }
