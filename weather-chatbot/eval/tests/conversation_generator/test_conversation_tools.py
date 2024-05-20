import unittest
from unittest.mock import patch
import json
import os
import pandas as pd


from eval.library.conversation_generator.conversation_tools import (
    generate_turn)


class TestConversationTools(unittest.TestCase):

    def test_generate_turn(self):
        context = {
            'message_history': [{'role': "assistant", 'content': "Hi"},
                                {'role': "user", 'content': "Hello"}],
            'pos_context': {'message_history': []},
            'conversation_id': '123',
            'scenario_prompt': '',
            'customer_profile': 'Profile'
        }

        with patch(
                'eval.library.conversation_generator.pos_harness.OrchestratorHarness') \
                as MockHarness, patch(
                'eval.library.conversation_generator.customer_chat.CustomerChat') as MockChat:

            harness_instance = MockHarness.return_value
            harness_instance.get_reply.return_value = 'pos_reply'
            pos = MockHarness()

            chat_instance = MockChat.return_value
            chat_instance.get_reply.return_value = 'user_reply'
            user = MockChat()

            generate_turn(pos, user, context)
            generate_turn(pos, user, context)

        # Expected context will lose the history each time because the mocked POS isn't populating
        # its own message_history. This is what would happen if the POS wiped message history at every turn.
        expected_context = {
            'message_history': [
                {'role': 'assistant', 'content': 'Hi'},
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'pos_reply', 'context':
                    {'message_history': [{'role': 'user', 'content': 'Hello'},
                                         {'role': 'assistant', 'content': 'pos_reply'}]}},
                {'role': 'user', 'content': 'user_reply'},
                {'role': 'assistant', 'content': 'pos_reply', 'context':
                    {'message_history': [{'role': 'user', 'content': 'user_reply'},
                                         {'role': 'assistant', 'content': 'pos_reply'}]}},
                {'role': 'user', 'content': 'user_reply'}],
            'pos_context': {'message_history': []},
            'conversation_id': '123',
            'scenario_prompt': '',
            'customer_profile': 'Profile'}

        self.assertEqual(context, expected_context)
