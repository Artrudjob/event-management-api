from django.db import transaction
from django.db.models import OuterRef, Prefetch, Subquery
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from events.filters import EventFilter
from events.models import Venue, Event
from events.permissions import IsSuperUser, IsSuperUserOrReadOnly
from events.serializers import EventImportFileSerializer, EventSerializer, VenueSerializer
from events.services.event_export_service import EventExportService
from events.services.event_import_service import EventImportService, EventXlsxParseError
from events.tasks import send_notification
from weather.models import Weather
from weather.tasks import fetch_weather_for_venue


class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.order_by("-id")
    serializer_class = VenueSerializer
    permission_classes = [IsSuperUser]

    def perform_create(self, serializer):
        venue = serializer.save()
        transaction.on_commit(lambda: fetch_weather_for_venue.delay(venue.pk))

class EventPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsSuperUserOrReadOnly]
    pagination_class = EventPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ["name", "venue__name"]
    ordering_fields = ["name", "starts_at", "ends_at"]
    ordering = ["-id"]

    def get_queryset(self):
        latest_weather_id = Subquery(
            Weather.objects.filter(venue_id=OuterRef("venue_id"))
            .order_by("-create_time", "-pk")
            .values("pk")[:1]
        )
        queryset = Event.objects.select_related("venue", "author").prefetch_related(
            "images",
            Prefetch(
                "venue__weathers",
                queryset=Weather.objects.filter(pk=latest_weather_id),
                to_attr="latest_weather_prefetched",
            ),
        )
        return self._visible_events(queryset)

    def _visible_events(self, queryset):
        user = self.request.user

        if user.is_authenticated and user.is_superuser:
            return queryset

        return queryset.filter(status=Event.Status.PUBLISHED)

    def perform_create(self, serializer):
        event = serializer.save(author=self.request.user)
        self._queue_publication_notification(event)

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        event = serializer.save()
        if previous_status != Event.Status.PUBLISHED:
            self._queue_publication_notification(event)

    def _queue_publication_notification(self, event: Event):
        if event.status != Event.Status.PUBLISHED:
            return

        transaction.on_commit(lambda: send_notification.delay(event.pk))

    @action(
        detail=False,
        methods=["post"],
        url_path="import",
        permission_classes=[IsSuperUser],
        parser_classes=[MultiPartParser, FormParser],
        serializer_class=EventImportFileSerializer,
    )
    def import_events(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = EventImportService().import_xlsx(serializer.validated_data["file"], author=request.user)
        except EventXlsxParseError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)

        if result["errors"]:
            return Response({"errors": result["errors"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"created": len(result["rows"])},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="export",
        permission_classes=[IsSuperUser],
        pagination_class=None,
    )
    def export_events(self, request):
        queryset = self.filter_queryset(
            self._visible_events(Event.objects.select_related("venue").order_by("-id"))
        )
        stream = EventExportService().export_xlsx(queryset)

        return FileResponse(
            stream,
            as_attachment=True,
            filename="events.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
