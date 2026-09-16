from rest_framework import viewsets
from rest_framework.permissions import BasePermission
from events.models import Venue
from events.serializers import VenueSerializer

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    permission_classes = [IsSuperUser]
