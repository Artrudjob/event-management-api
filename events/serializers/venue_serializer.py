from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from events.models import Venue
from weather.serializers import WeatherSerializer


class VenueSerializer(serializers.ModelSerializer):
    weather = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = ["id", "name", "latitude", "longitude", "weather"]

    @extend_schema_field(WeatherSerializer(allow_null=True))
    def get_weather(self, obj):
        prefetched = getattr(obj, "latest_weather_prefetched", None)

        if prefetched is not None:
            last_weather = prefetched[0] if prefetched else None
        else:
            last_weather = obj.weathers.order_by("-create_time").first()

        if last_weather:
            return WeatherSerializer(last_weather).data

        return None
