import random
from decimal import Decimal

from weather.providers.base import WeatherProvider, WeatherSnapshot


class MockWeatherProvider(WeatherProvider):
    def get_current_weather(self, latitude, longitude) -> WeatherSnapshot:
        return WeatherSnapshot(
            temperature_in_c=random.randint(-40, 40),
            humidity=random.randint(10, 100),
            pressure=random.randint(720, 780),
            wind_direction=random.randint(0, 360),
            wind_speed=Decimal(str(round(random.uniform(0, 20), 1))),
        )
