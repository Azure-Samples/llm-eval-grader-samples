import requests
import os
import logging
from enum import Enum
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

BASE_WEATHER_URI = "https://atlas.microsoft.com/weather/"
FORMAT = "json"
API_VERSION = "1.0"


class WeatherType(Enum):
    CURRENT = "currentConditions/"
    DAILY_FORECAST = "forecast/daily/"
    SEVERE_ALERTS = "severe/alerts/"


class Weather():
    @staticmethod
    def get_weather(lat: float, lon: float, weather_type: WeatherType) -> str:

        if not Weather._is_float(lat) or not Weather._is_float(lon):
            return f"Coordinates must be valid floats: received lat: {lat} lon: {lon}"

        if not -90 <= float(lat) <= 90 or not -180 <= float(lon) <= 180:
            return f"Coordinates out of range: received lat {lat} lon {lon}, " \
                "range for lat -90 - 90, range for lon -180 - 180"

        try:
            response = requests.get(BASE_WEATHER_URI + weather_type.value + FORMAT,
                                    params={"api-version": API_VERSION,
                                            "query": f"{lat}, {lon}",
                                            "subscription-key": os.environ['MAPS_API_KEY']})
            response.raise_for_status()

        except HTTPError as ex:
            logger.exception(ex)
            raise ex

        return response.content

    @staticmethod
    def _is_float(num: str) -> bool:
        """
        Simple check for float, doesn't determine
        whether values are valid coordinates
        """
        try:
            float(num)
            return True
        except ValueError:
            return False
