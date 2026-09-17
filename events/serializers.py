from rest_framework import serializers
from events.models import Venue, Event, EventImage
from weather.models import Weather
from django.core.exceptions import ValidationError
from django.utils import timezone


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

class VenueSerializer(serializers.ModelSerializer):
    weather = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = ["id", "name", "latitude", "longitude", "weather"]

    def get_weather(self, obj):
        prefetched = getattr(obj, "latest_weather_prefetched", None)

        if prefetched is not None:
            last_weather = prefetched[0] if prefetched else None
        else:
            last_weather = obj.weathers.order_by("-create_time").first()

        if last_weather:
            return WeatherSerializer(last_weather).data

        return None

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ["id", "image", "preview"]
        read_only_fields = ["preview"]

class EventSerializer(serializers.ModelSerializer):
    images = EventImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=100, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
        label="Изображения"
    )
    venue_detail = VenueSerializer(source="venue", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "description",
            "starts_at",
            "ends_at",
            "venue",
            "rating",
            "status",
            "images",
            "uploaded_images",
            "venue_detail",
            "publication_at",
            "author",
        ]
        read_only_fields = ["author", "status", "create_time", "update_time"]

    def validate(self, data):
        extra_fields = {"uploaded_images"}
        model_data = {key: value for key, value in data.items() if key not in extra_fields}

        if self.instance is not None:
            instance = self.instance
        else:
            instance = Event()

        for field, value in model_data.items():
            setattr(instance, field, value)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return data

    def save_images(self, event, uploaded_images):
        for image in uploaded_images:
            EventImage.objects.create(event=event, image=image)

    def set_publication_at(self, validated_data, instance=None):
        publication_at = validated_data.get("publication_at")

        if publication_at is None:
            publication_at = instance.publication_at

        if publication_at < timezone.now():
            validated_data["status"] = Event.Status.DRAFT
        else:
            validated_data["status"] = Event.Status.PUBLISHED

    def prepare_save_data(self, validated_data, instance=None):
        uploaded_images = validated_data.pop("uploaded_images", [])
        self.set_publication_at(validated_data, instance)

        return uploaded_images

    def create(self, validated_data):
        uploaded_images = self.prepare_save_data(validated_data)
        event = Event.objects.create(**validated_data)
        self.save_images(event, uploaded_images)

        return event

    def update(self, instance, validated_data):
        uploaded_images = self.prepare_save_data(validated_data, instance)
        self.set_publication_at(validated_data, instance)

        event = super().update(instance, validated_data)
        self.save_images(event, uploaded_images)

        return event