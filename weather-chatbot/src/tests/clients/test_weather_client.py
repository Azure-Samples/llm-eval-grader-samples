import unittest
import json
from logging import Logger
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import HTTPError
from requests import Response

from clients.weather import Weather, WeatherType


class TestWeatherClient(unittest.TestCase):
    @patch("clients.weather.logger")
    @patch("clients.weather.requests")
    @patch("requests.Response")
    def test_get_weather_valid_coords_returns_valid_content(self, mock_response: Mock, mock_requests: Mock,
                                                                    mock_logger: Mock):

        mock_response.status_code = 200

        mock_response.content = '{"results": [{"temperature": {"value": 15.0, "unit": "C", "unitType": 17}}]}'

        mock_requests.get.return_value = mock_response

        current_weather = Weather.get_weather(lat="45.6579106", lon="-122.5834869", type=WeatherType.CURRENT)

        self.assertNotEqual(current_weather, "")
        self.assertNotEqual(current_weather, None)
        self.assertIsInstance(current_weather, str)
        self.assertEqual(json.loads(current_weather)["results"][0]["temperature"]["value"], 15.0)

    def test_get_weather_invalid_coords_returns_invalid_message(self):

        current_weather = Weather.get_weather(lat="45.6579106a", lon="+122", type=WeatherType.CURRENT)

        self.assertEqual(current_weather, "Coordinates must be valid floats")

    def test_get_weather_coords_out_of_range_returns_invalid_message(self):

        current_weather = Weather.get_weather(lat="45.6579106", lon="189", type=WeatherType.CURRENT)

        self.assertEqual(current_weather, "Coordinates out of range")

    @patch("clients.weather.logger")
    @patch("clients.weather.requests")
    @patch("requests.Response")
    def test_get_weather_error_response_throws_exception(self, mock_response: Mock, mock_requests: Mock, mock_logger: Mock):
        fake_response = Response()
        fake_response.status_code = 500
        fake_response.reason = 'Internal Server Error'

        mock_requests.get.return_value = fake_response
        
        #make sure to throw exception before you check to see if logger.exception called
        self.assertRaises(HTTPError, Weather.get_weather, lat="45.6579106", lon="-122.5834869", type=WeatherType.CURRENT)
        mock_logger.exception.assert_called_once()