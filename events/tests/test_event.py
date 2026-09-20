import pytest
from django.urls import reverse
from rest_framework import status
from events.models import Event

def _list_results(response):
    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]
    return response.data

@pytest.mark.django_db
@pytest.mark.parametrize(
    "client_name,has_permission_view",
    [
        ("superuser_client", True),
        ("user_client", False),
    ],
    ids=["superuser", "user"],
)
class TestEventReadPermissions:
    """Ожидается, что суперпользователь видит все мероприятия, остальные только опубликованные."""

    def test_get_list(
        self,
        request,
        client_name,
        has_permission_view,
        published_event,
        draft_event,
    ):
        client = request.getfixturevalue(client_name)
        response = client.get(reverse("event-list"))
        results = _list_results(response)
        ids = {item["id"] for item in results}

        assert response.status_code == status.HTTP_200_OK
        assert published_event.pk in ids

        if has_permission_view:
            assert draft_event.pk in ids
            assert len(results) == 2
        else:
            assert draft_event.pk not in ids
            assert len(results) == 1

    def test_get_draft_detail(
        self,
        request,
        client_name,
        has_permission_view,
        draft_event,
    ):
        client = request.getfixturevalue(client_name)
        response = client.get(
            reverse("event-detail", kwargs={"pk": draft_event.pk}),
        )

        if has_permission_view:
            assert response.status_code == status.HTTP_200_OK
            assert response.data["id"] == draft_event.pk
        else:
            assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
@pytest.mark.parametrize(
    "client_name",
    ["superuser_client", "user_client"],
    ids=["superuser", "user"],
)
class TestEventPublishedReadPermissions:
    """Ожидается, что опубликованное мероприятие доступно и суперпользователю, и обычному."""

    def test_get_published_detail(self, request, client_name, published_event):
        client = request.getfixturevalue(client_name)
        response = client.get(
            reverse("event-detail", kwargs={"pk": published_event.pk}),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == published_event.pk

@pytest.mark.django_db
@pytest.mark.parametrize(
    "client_name,is_permitted",
    [
        ("superuser_client", True),
        ("user_client", False),
    ],
    ids=["superuser", "user"],
)
class TestEventWritePermissions:
    """Ожидается, что создание, редактирование и удаление доступно только суперпользователю."""

    def test_create(
        self,
        request,
        client_name,
        is_permitted,
        event_payload,
    ):
        client = request.getfixturevalue(client_name)
        response = client.post(
            reverse("event-list"),
            event_payload,
            format="json",
        )

        if is_permitted:
            assert response.status_code == status.HTTP_201_CREATED
            assert Event.objects.filter(name=event_payload["name"]).exists()
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert not Event.objects.filter(name=event_payload["name"]).exists()

    def test_update(
        self,
        request,
        client_name,
        is_permitted,
        published_event,
    ):
        client = request.getfixturevalue(client_name)
        event_name = published_event.name
        payload = {"name": "Опубликованное мероприятие (update)"}
        response = client.patch(
            reverse("event-detail", kwargs={"pk": published_event.pk}),
            payload,
            format="json",
        )

        published_event.refresh_from_db()

        if is_permitted:
            assert response.status_code == status.HTTP_200_OK
            assert published_event.name == payload["name"]
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert published_event.name == event_name

    def test_delete(
        self,
        request,
        client_name,
        is_permitted,
        published_event,
    ):
        client = request.getfixturevalue(client_name)
        response = client.delete(
            reverse("event-detail", kwargs={"pk": published_event.pk}),
        )

        if is_permitted:
            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert not Event.objects.filter(pk=published_event.pk).exists()
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert Event.objects.filter(pk=published_event.pk).exists()

@pytest.mark.django_db
@pytest.mark.parametrize(
    "client_name,is_permitted",
    [
        ("superuser_client", True),
        ("user_client", False),
    ],
    ids=["superuser", "user"],
)
class TestEventExportPermissions:
    """Ожидается, что экспорт мероприятий доступен только суперпользователю."""

    def test_export(self, request, client_name, is_permitted, published_event):
        client = request.getfixturevalue(client_name)
        response = client.get(reverse("event-export-events"))

        if is_permitted:
            assert response.status_code == status.HTTP_200_OK
            assert (
                response["Content-Type"]
                == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestEventDateValidation:
    """Ожидается, что нельзя создать мероприятие, если начало позже окончания."""

    def test_reject_invalid_interval(
        self,
        superuser_client,
        event_payload,
    ):
        event_payload["starts_at"] = event_payload["ends_at"]
        response = superuser_client.post(
            reverse("event-list"),
            event_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "starts_at" in response.data
        assert not Event.objects.filter(name=event_payload["name"]).exists()
