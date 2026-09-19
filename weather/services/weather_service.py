import logging
from dataclasses import asdict
from events.models import Venue
from weather.models import Weather
from weather.providers import MockWeatherProvider, WeatherProvider

logger = logging.getLogger(__name__)

class WeatherService:
    CHUNK_SIZE = 100

    def __init__(self, provider: WeatherProvider | None = None):
        self.provider = provider or MockWeatherProvider()

    def fetch_for_venue(self, venue: Venue) -> Weather:
        weather_data = self.provider.get_current_weather(venue.latitude, venue.longitude)

        return Weather.objects.create(venue=venue, **asdict(weather_data))

    def fetch_for_all_venues(self) -> list[Weather]:
        created = []

        for venue in Venue.objects.all().iterator(chunk_size=self.CHUNK_SIZE):
            try:
                created.append(self.fetch_for_venue(venue))
            except Exception:
                logger.exception("Не удалось сохранить погоду для venue id=%s", venue.pk)

        return created
