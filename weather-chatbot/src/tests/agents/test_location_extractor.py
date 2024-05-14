import unittest
from unittest.mock import Mock, patch

from agents.location.location_extractor import LocationExtractor


class TestLocationExtractor(unittest.TestCase):
    def test_get_last_user_message(self):
        extractor = LocationExtractor()

        message_history = [{'role': 'assistant', 'content': 'Hi! How can I help you'}]
        last_user_message = extractor.get_last_user_message(message_history)
        assert last_user_message is None

        user_message = 'This is some test message'
        message_history += [{'role': 'user', 'content': user_message}]
        last_user_message = extractor.get_last_user_message(message_history)
        assert last_user_message['content'] is user_message
