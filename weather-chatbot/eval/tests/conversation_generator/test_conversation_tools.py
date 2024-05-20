import unittest
from unittest.mock import patch
import json
import os
import pandas as pd


from eval.library.conversation_generator.conversation_tools import (
    write_conversation_to_logs,
    write_conversation_to_condensed_logs,
    generate_turn)


class TestConversationTools(unittest.TestCase):
    def test_write_conversation_to_logs(self):
        # Define test data
        message_history = [
            {'text': 'Hello'},
            {'text': 'How are you?', 'context': {'message_history': [{'text': 'Hello'}]}},
            {'text': 'I am good. How about you?', 'context': {'message_history':
                                                              [{'text': 'Hello'}, {'text': 'How are you?'}]}}
        ]
        conversation_id = "123456"
        customer_profile = {"name": "John Doe", "age": 25}
        scenario_prompt = "Customer support"
        log_file_name = "src/tests/unit/eval/data/test_write_conversation_to_logs_log_file.json"
        convo_end_reason = 'dummy reason'

        # Call the function being tested
        write_conversation_to_logs(message_history, conversation_id, customer_profile,
                                   scenario_prompt, log_file_name, convo_end_reason)

        # Read in conversation
        with open(log_file_name, "r") as file:
            file_contents = file.read()
            json_objects = file_contents.split('~~~NEW_CONVERSATION~~~')

        conversation = {}
        for obj in json_objects:
            try:
                conversation = json.loads(obj)
                if isinstance(conversation, dict):
                    break
            except json.JSONDecodeError:
                pass

        # Validate data
        self.assertEqual(conversation['conversation_id'], conversation_id)
        self.assertEqual(conversation['customer_profile'], customer_profile)
        self.assertEqual(conversation['scenario_prompt'], scenario_prompt)
        self.assertEqual(len(conversation['conversation_history']), len(message_history))

        # Clean up by deleting file
        if os.path.exists(log_file_name):
            os.remove(log_file_name)

    def test_write_conversation_to_condensed_logs(self):
        # Define test data
        message_history = [
            {'role': 'role1', 'content': 'Hello'},
            {'role': 'role2', 'content': 'Hi'},
        ]
        conversation_id = "123456"
        customer_profile = {'attributes': {"vehicle": 'vehicle',
                                           "name": "John Doe",
                                           "age": 25,
                                           'tire_category': ['Winter Tires']},
                            }
        scenario_prompt = "Customer support"
        convo_end_reason = "dummy reason"
        log_file_name = "eval/tests/data/test_write_conversation_to_condensed_logs_log_file.xlsx"

        # Call the function being tested
        write_conversation_to_condensed_logs(message_history, conversation_id, customer_profile, scenario_prompt,
                                             log_file_name, convo_end_reason)

        # Read in output file
        df = pd.read_excel(log_file_name, engine='openpyxl')
        self.assertEqual(len(df), len(message_history))

        # Clean up by deleting file
        if os.path.exists(log_file_name):
            os.remove(log_file_name)

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
