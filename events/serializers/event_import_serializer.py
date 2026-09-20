from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from events.constants import XlsxFieldConstants
from events.models import Event, Venue

class EventImportFileSerializer(serializers.Serializer):
    file = serializers.FileField()

class EventImportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
        default=""
    )
    publication_at = serializers.DateTimeField()
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    venue_name = serializers.CharField(max_length=255)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    rating = serializers.IntegerField(min_value=0, max_value=25)

    def validate(self, data: dict) -> dict:
        errors = {}
        errors.update(self._get_venue_errors(data))
        errors.update(self._get_event_errors(data))

        if errors:
            raise serializers.ValidationError(errors)

        data[XlsxFieldConstants.STATUS] = self._set_event_status(data[XlsxFieldConstants.PUBLICATION_AT])

        return data

    def _get_venue_errors(self, data: dict) -> dict:
        venue = Venue.objects.filter(name=data[XlsxFieldConstants.VENUE_NAME]).first()

        if venue is None:
            venue = Venue(name=data[XlsxFieldConstants.VENUE_NAME])

        venue.latitude = data[XlsxFieldConstants.LATITUDE]
        venue.longitude = data[XlsxFieldConstants.LONGITUDE]

        try:
            venue.full_clean()
        except ValidationError as exc:
            return self._transform_venue_errors(exc)

        return {}

    def _get_event_errors(self, data: dict) -> dict:
        event = Event(
            name=data[XlsxFieldConstants.NAME],
            description=data.get(XlsxFieldConstants.DESCRIPTION, ""),
            publication_at=data[XlsxFieldConstants.PUBLICATION_AT],
            starts_at=data[XlsxFieldConstants.STARTS_AT],
            ends_at=data[XlsxFieldConstants.ENDS_AT],
            rating=data[XlsxFieldConstants.RATING],
        )
        try:
            event.clean()
        except ValidationError as exc:
            return exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}

        return {}

    def _transform_venue_errors(self, exc: ValidationError) -> dict:
        field_map = {"name": XlsxFieldConstants.VENUE_NAME}
        if not hasattr(exc, "message_dict"):
            return {"venue_non_field_errors": exc.messages}

        return {
            field_map.get(field, field): messages
            for field, messages in exc.message_dict.items()
        }

    def _set_event_status(self, publication_at) -> str:
        if publication_at <= timezone.now():
            return Event.Status.PUBLISHED

        return Event.Status.DRAFT
