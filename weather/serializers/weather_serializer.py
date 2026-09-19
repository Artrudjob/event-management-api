from rest_framework import serializers

from weather.models import Weather


class WeatherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Weather
        fields = [
            "temperature_in_c",
            "humidity",
            "pressure",
            "wind_direction",
            "wind_speed",
        ]
