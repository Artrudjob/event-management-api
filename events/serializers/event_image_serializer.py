from rest_framework import serializers

from events.models import EventImage


class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ["id", "image", "preview"]
        read_only_fields = ["preview"]
