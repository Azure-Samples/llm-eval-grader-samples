import unittest
from unittest.mock import patch, Mock
from copy import deepcopy
import os
import json
import pytest
from eval.library.conversation_generator.customer_chat import CustomerChat


class TestCustomerChat(unittest.TestCase):
    @pytest.fixture(scope='module', autouse=True)
    def setup(self):
        """ Set mock environment variables needed for each test """
        env_path = 'eval/tests/data/dummy_env.json'
        with open(env_path, 'r') as f_p:
            mock_variables = json.load(f_p)

        with patch.dict(os.environ, mock_variables):
            yield

    def test_get_reply(self):
        mock_response_text = 'customer text response'
        with patch(
                'eval.library.conversation_generator.customer_chat.get_completion') \
                as mock_get_completion, \
                patch('eval.library.conversation_generator.customer_chat.'
                      'CustomerChat.get_system_message', return_value=''):

            # Configure the mock behavior
            mock_get_completion.return_value = mock_response_text
            instance = mock_get_completion.return_value

            # Initialize class
            customer_chat = CustomerChat()

            # Set context and make a deepycopy
            context = {
                'message_history': [{'role': "assistant", 'content': "Hi. I am assistant"},
                                    {'role': "user", 'content': "Hello. I am an emulated user"}],
                'assistantHarness_context': {'message_history': []},
                'conversation_id': '123',
                'customer_profile': {'prompt': 'customer prompt'}
            }
            expected_context = deepcopy(context)

            # Get completion
            reply = customer_chat.get_reply(context=context)

            # Test that context is not changed
            self.assertEqual(context, expected_context)

            # Test that the response returned by Open AI is returned by the customer chat object
            self.assertEqual(reply, mock_response_text)

            # The emulated user flips the assistant/user order around
            # so that the emulated user messages are from the
            # assistant and the user it's talking to is actually assistant
            for message in context['message_history']:
                if message['role'] == 'assistant':
                    message['role'] = 'user'
                elif message['role'] == 'user':
                    message['role'] = 'assistant'

            mock_get_completion.assert_called_once_with(
                messages=context['message_history'],
                temperature=customer_chat.temperature
            )
