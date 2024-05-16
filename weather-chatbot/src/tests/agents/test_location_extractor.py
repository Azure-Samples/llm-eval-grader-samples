import os
import unittest
from unittest.mock import Mock, patch, ANY

from azure.maps.search.models import LatLon

from agents.location.location_extractor import LocationExtractor
from context import Context


class TestLocationExtractor(unittest.TestCase):
    @patch.dict(os.environ, {"OPENAI_DEPLOYMENT_NAME": "openai_deployment_name"})
    @patch.dict(os.environ, {"MAPS_API_KEY": "maps_api_key"})
    @patch('agents.location.location_extractor.AzureOpenAI')
    @patch('agents.location.location_extractor.MapsSearchClient.search_address')
    def test_extract(self, search_address_mock, openai_mock):
        address = Mock(
            type='Point Address',
            position=LatLon(lat=47.6062, lon=122.3321),
            score=1,
            address=Mock(country='US', freeform_address='Seattle'))

        search_address_mock.return_value.results = [address]

        openai_mock().chat.completions.create.return_value.choices[0].message.content = 'Seattle'

        extractor = LocationExtractor()

        message_history = [
            {'role': 'assistant', 'content': 'Hi! What is your location?'},
            {'role': 'user', 'content': 'I live in Seattle'},
        ]

        context = Context()
        context._messages = message_history

        extractor.extract(context)

        self.assertEqual((47.6062, 122.3321), context.location)
        self.assertEqual("US, Seattle", context.location_description)

        openai_mock().chat.completions.create.assert_called_once_with(
            temperature=0,
            model='openai_deployment_name',
            messages=[
                {'role': 'system', 'content': ANY},
            ]
        )
