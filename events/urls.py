from django.urls import path, include
from rest_framework import routers
from events.views import VenueViewSet

router = routers.DefaultRouter()
router.register(r"venues", VenueViewSet, basename="venue")

urlpatterns = [path("", include(router.urls))]