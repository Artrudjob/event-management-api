from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from events.models import Event, EventImage
from events.serializers.event_image_serializer import EventImageSerializer
from events.serializers.venue_serializer import VenueSerializer


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

    def create(self, validated_data):
        uploaded_images = self._prepare_save_data(validated_data)
        event = Event.objects.create(**validated_data)
        self._save_images(event, uploaded_images)

        return event

    def update(self, instance, validated_data):
        uploaded_images = self._prepare_save_data(validated_data, instance)
        self._set_publication_at(validated_data, instance)

        event = super().update(instance, validated_data)
        self._save_images(event, uploaded_images)

        return event

    def _save_images(self, event, uploaded_images):
        for image in uploaded_images:
            EventImage.objects.create(event=event, image=image)

    def _set_publication_at(self, validated_data, instance=None):
        publication_at = validated_data.get("publication_at")

        if publication_at is None:
            publication_at = instance.publication_at

        if publication_at <= timezone.now():
            validated_data["status"] = Event.Status.PUBLISHED
        else:
            validated_data["status"] = Event.Status.DRAFT

    def _prepare_save_data(self, validated_data, instance=None):
        uploaded_images = validated_data.pop("uploaded_images", [])
        self._set_publication_at(validated_data, instance)

        return uploaded_images
