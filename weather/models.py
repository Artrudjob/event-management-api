from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from events.models import Venue

class Weather(models.Model):
    """Погода в месте проведения мероприятия"""

    temperature_in_c = models.IntegerField(
        validators=[MinValueValidator(-100), MaxValueValidator(100)],
        verbose_name="Температура по шкале Цельсия",
    )
    humidity = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Влажность воздуха, в %",
    )
    pressure = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Атмосферное давление, в мм ртутного столба",
    )
    wind_direction = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        verbose_name="Направление ветра",
    )
    wind_speed = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0.0"))],
        verbose_name="Скорость ветра, в м/с",
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name="weathers",
        verbose_name="Место проведения",
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self):
        return f"Погода для {self.venue_id} на ({self.create_time})"
