from celery import shared_task

from events.models import Venue
from weather.services import WeatherService


@shared_task
def fetch_weather_for_all_venues():
    WeatherService().fetch_for_all_venues()

@shared_task
def fetch_weather_for_venue(venue_id: int):
    venue = Venue.objects.get(pk=venue_id)
    WeatherService().fetch_for_venue(venue)
