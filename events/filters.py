from django_filters import rest_framework as filters
from events.models import Event, Venue

class EventFilter(filters.FilterSet):
    starts_at = filters.IsoDateTimeFromToRangeFilter()
    ends_at = filters.IsoDateTimeFromToRangeFilter()
    venue = filters.ModelMultipleChoiceFilter(queryset=Venue.objects.all())
    rating = filters.RangeFilter()

    class Meta:
        model = Event
        fields = ["starts_at", "ends_at", "venue", "rating"]
