from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class WeatherSnapshot:
    temperature_in_c: int
    humidity: int
    pressure: int
    wind_direction: int
    wind_speed: Decimal

class WeatherProvider(ABC):
    @abstractmethod
    def get_current_weather(self, latitude, longitude) -> WeatherSnapshot:
        pass