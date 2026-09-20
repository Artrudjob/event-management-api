from django.db import transaction
from django.db.models import OuterRef, Prefetch, Subquery
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
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

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@extend_schema(tags=["venues"])
@extend_schema_view(
    list=extend_schema(summary="Получить список мест проведения мероприятий"),
    retrieve=extend_schema(summary="Получить место проведения мероприятия"),
    create=extend_schema(summary="Создать место проведения мероприятия"),
    update=extend_schema(summary="Обновить место проведения мероприятия"),
    partial_update=extend_schema(summary="Обновить (частично) место проведения мероприятия"),
    destroy=extend_schema(summary="Удалить место проведения мероприятия"),
)
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

@extend_schema(tags=["events"])
@extend_schema_view(
    list=extend_schema(summary="Получить список мероприятий"),
    retrieve=extend_schema(summary="Получить мероприятие"),
    create=extend_schema(summary="Создать мероприятие"),
    update=extend_schema(summary="Обновить мероприятие"),
    partial_update=extend_schema(summary="Обновить (частично) мероприятие"),
    destroy=extend_schema(summary="Удалить мероприятие"),
)
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

    @extend_schema(
        summary="Импорт мероприятий из файла .xlsx",
        request=EventImportFileSerializer,
        responses={
            201: inline_serializer(
                name="EventImportCreated",
                fields={"created": serializers.IntegerField()},
            ),
            400: inline_serializer(
                name="EventImportFailed",
                fields={
                    "detail": serializers.CharField(required=False),
                    "errors": serializers.ListField(required=False),
                },
            ),
            403: OpenApiResponse(description="Доступ только для суперпользователя"),
        },
    )
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

    @extend_schema(
        summary="Экспорт мероприятий в файла .xlsx",
        responses={
            (200, XLSX_CONTENT_TYPE): OpenApiTypes.BINARY,
            403: OpenApiResponse(description="Доступ только для суперпользователя"),
        },
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
            content_type=XLSX_CONTENT_TYPE,
        )
