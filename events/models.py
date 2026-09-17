import uuid
from io import BytesIO
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from decimal import Decimal
from PIL import Image
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

class Venue(models.Model):
    """Место проведения мероприятия"""

    name = models.CharField(max_length=255, verbose_name="Название места")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("-90.000000")), MaxValueValidator(Decimal("90.000000"))],
        verbose_name="Широта"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("-180.000000")), MaxValueValidator(Decimal("180.000000"))],
        verbose_name="Долгота"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    update_time = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

class Event(models.Model):
    """Мероприятие"""

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"

    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(default="", verbose_name="Описание")
    publication_at = models.DateTimeField(verbose_name="Дата и время публикации")
    starts_at = models.DateTimeField(verbose_name="Дата и время начала проведения")
    ends_at = models.DateTimeField(verbose_name="Дата и время завершения проведения")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Автор"
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="Место проведения"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(25)],
        verbose_name="Рейтинг"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Статус"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    update_time = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    def check_date_interval(self):
        if (
            self.starts_at
            and self.ends_at
            and self.starts_at >= self.ends_at
        ):
            raise ValidationError({
                "starts_at": "Дата и время начала проведения не может начинаться позже даты и времени окончания."
            })

    def clean(self):
        super().clean()
        self.check_date_interval()

class EventImage(models.Model):
    """Изображение мероприятия"""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Мероприятие"
    )
    image = models.ImageField(upload_to="events/images/", verbose_name="Изображение")
    preview = models.ImageField(
        upload_to="events/previews/",
        blank=True,
        null=True,
        verbose_name="Превью"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Изображение для {self.event.name}"

    def save(self, *args, **kwargs):
        if self.pk:
            original = EventImage.objects.get(pk=self.pk)

            if original.image != self.image:
                self.make_preview()
        else:
            if self.image and not self.preview:
                self.make_preview()

        super().save(*args, **kwargs)

    def make_preview(self):
        with Image.open(self.image) as image:
            width, height = image.size
            target_size = 200

            if min(width, height) > target_size:
                if width < height:
                    new_width = target_size
                    new_height = int(height * (target_size / width))
                else:
                    new_height = target_size
                    new_width = int(width * (target_size / height))
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")

            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

        file_name = f"preview_{uuid.uuid4().hex}.jpg"
        self.preview.save(file_name, ContentFile(buffer.read()), save=False)