from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from decimal import Decimal

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
        return f"{self.name}"