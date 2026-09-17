from django.urls import path, include
from rest_framework import routers
from events.views import VenueViewSet, EventViewSet

router = routers.DefaultRouter()
router.register(r"venues", VenueViewSet, basename="venue")
router.register(r"events", EventViewSet, basename="event")

urlpatterns = [path("", include(router.urls))]