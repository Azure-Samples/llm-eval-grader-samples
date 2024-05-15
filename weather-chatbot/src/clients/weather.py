import requests
import os
import logging
from dotenv import load_dotenv
from enum import Enum
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

load_dotenv()

MAPS_API_KEY = os.getenv('MAPS_API_KEY')
BASE_WEATHER_URI = "https://atlas.microsoft.com/weather/"
FORMAT = "json"
API_VERSION = "1.0"

class WeatherType(Enum):
    CURRENT = "currentConditions/"
    DAILY_FORECAST = "forecast/daily/"
    SEVERE_ALERTS = "severe/alerts/"

class Weather():
    @staticmethod
    def get_weather(lat: str, lon: str, type: WeatherType) -> str:

        if not Weather._is_float(lat) or not Weather._is_float(lon):
            return "Coordinates must be valid floats"
        
        if not -90 <= float(lat) <= 90 or not -180 <= float(lon) <=180:
            return "Coordinates out of range"
        
        try:
            response = requests.get(BASE_WEATHER_URI + type.value + FORMAT,
                                    params={"api-version": API_VERSION,
                                        "query": f"{lat}, {lon}",
                                        "subscription-key": MAPS_API_KEY})
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