import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from events.models import Venue

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
