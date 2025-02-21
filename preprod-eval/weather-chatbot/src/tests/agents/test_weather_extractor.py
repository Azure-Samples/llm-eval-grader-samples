# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import unittest
from unittest.mock import patch, ANY
from unittest import mock

from src.agents.weather.weather_extractor import WeatherExtractor, UNKNOWN_CATEGORY
from src.clients.weather import WeatherType
from src.context import Context


@mock.patch.dict(os.environ, {"OPENAI_DEPLOYMENT_NAME": "openai_deployment_name"})
@mock.patch.dict(os.environ, {"MAPS_API_KEY": "FAKE_KEY"})
class TestWeatherExtractor(unittest.TestCase):

    @patch('src.agents.weather.weather_extractor.AzureOpenAI')
    def test_extract_valid_weather_type_adds_type_to_context(self, openai_mock):

        openai_mock().chat.completions.create.return_value.choices[0]\
            .message.content = WeatherType.CURRENT_CONDITIONS.name

        extractor = WeatherExtractor()

        message_history = [
            {'role': 'assistant', 'content': 'Hi! What is your location?'},
            {'role': 'user', 'content': 'I live in Seattle and would like to know about the current weather'},
        ]

        context = Context()
        context._messages = message_history

        extractor.extract(context)

        self.assertEqual(WeatherType.CURRENT_CONDITIONS, context.weather_category)

        openai_mock().chat.completions.create.assert_called_once_with(
            temperature=0,
            model='openai_deployment_name',
            messages=[
                {'role': 'system', 'content': ANY},
            ]
        )

    @patch('src.agents.weather.weather_extractor.AzureOpenAI')
    def test_extract_no_weather_type_type_not_added_to_context(self, openai_mock):

        openai_mock().chat.completions.create.return_value.choices[0]\
            .message.content = UNKNOWN_CATEGORY

        extractor = WeatherExtractor()

        message_history = [
            {'role': 'assistant', 'content': 'Hi! What is your location?'},
            {'role': 'user', 'content': 'I live in Seattle'},
        ]

        context = Context()
        context._messages = message_history

        extractor.extract(context)

        self.assertEqual(None, context.weather_category)

        openai_mock().chat.completions.create.assert_called_once_with(
            temperature=0,
            model='openai_deployment_name',
            messages=[
                {'role': 'system', 'content': ANY},
            ]
        )
