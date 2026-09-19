import pytest
from django.urls import reverse
from rest_framework import status
from events.models import Venue

@pytest.mark.django_db
@pytest.mark.parametrize(
    "client_name,is_permitted",
    [
        ("superuser_client", True),
        ("user_client", False),
    ],
    ids=["superuser", "user"],
)
class TestVenueCrud:
    """CRUD для мест проведения мероприятий: проверка прав доступа."""

    def test_get_list(
        self,
        request,
        client_name,
        is_permitted,
        venue,
    ):
        client = request.getfixturevalue(client_name)
        response = client.get(reverse("venue-list"))

        if is_permitted:
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1
            assert response.data[0]["id"] == venue.pk
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_detail(
        self,
        request,
        client_name,
        is_permitted,
        venue,
    ):
        client = request.getfixturevalue(client_name)
        response = client.get(
            reverse("venue-detail", kwargs={"pk": venue.pk}),
        )

        if is_permitted:
            assert response.status_code == status.HTTP_200_OK
            assert response.data["id"] == venue.pk
            assert response.data["name"] == venue.name
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create(
        self,
        request,
        client_name,
        is_permitted,
        venue_payload
    ):
        client = request.getfixturevalue(client_name)
        response = client.post(
            reverse("venue-list"),
            venue_payload,
            format="json",
        )

        if is_permitted:
            assert response.status_code == status.HTTP_201_CREATED
            assert Venue.objects.filter(name=venue_payload["name"]).exists()
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert not Venue.objects.filter(name=venue_payload["name"]).exists()

    def test_update(
        self,
        request,
        client_name,
        is_permitted,
        venue,
    ):
        client = request.getfixturevalue(client_name)
        venue_name = venue.name
        payload = {"name": "Тест место (update)"}
        response = client.patch(
            reverse("venue-detail", kwargs={"pk": venue.pk}),
            payload,
            format="json",
        )

        venue.refresh_from_db()

        if is_permitted:
            assert response.status_code == status.HTTP_200_OK
            assert venue.name == payload["name"]
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert venue.name == venue_name

    def test_delete(
        self,
        request,
        client_name,
        is_permitted,
        venue
    ):
        client = request.getfixturevalue(client_name)
        response = client.delete(reverse("venue-detail", kwargs={"pk": venue.pk}))

        if is_permitted:
            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert not Venue.objects.filter(pk=venue.pk).exists()
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert Venue.objects.filter(pk=venue.pk).exists()
