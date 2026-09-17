from django.db.models import OuterRef, Prefetch, Subquery
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, SAFE_METHODS
from events.filters import EventFilter
from events.models import Venue, Event
from events.serializers import VenueSerializer, EventSerializer
from weather.models import Weather

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )

class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )

class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.order_by("-id")
    serializer_class = VenueSerializer
    permission_classes = [IsSuperUser]

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
        user = self.request.user

        if user.is_authenticated and user.is_superuser:
            return queryset

        return queryset.filter(status = Event.Status.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
