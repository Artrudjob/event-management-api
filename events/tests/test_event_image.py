import pytest
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from events.models import EventImage

def _jpeg_file(width, height, name="photo.jpg"):
    buffer = BytesIO()
    Image.new("RGB", (width, height), "red").save(buffer, format="JPEG")
    buffer.seek(0)

    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")

@pytest.mark.django_db
class TestEventImagePreview:
    """Ожидается, что превью уменьшается до 200px по меньшей стороне."""

    def test_reduce_preview(self, published_event, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        event_image = EventImage.objects.create(
            event=published_event,
            image=_jpeg_file(400, 800),
        )

        assert event_image.preview
        with Image.open(event_image.preview.path) as preview:
            assert min(preview.size) == 200
