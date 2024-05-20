import unittest
from unittest.mock import patch
from copy import deepcopy
from eval.library.conversation_generator.pos_harness import PromptOrchestratorHarness


class TestPosHarness(unittest.TestCase):
    def test_get_reply(self):
        with patch(
                'src.orchestrator.Orchestrator', autospec=True) \
                as MockOrchestrator, patch(
                'eval.library.conversation_generator.pos_harness.get_first_text_ai_response') \
                as mock_first_text:

            # Configure the mock behavior
            instance = MockOrchestrator.return_value
            instance.get_reply.return_value = ['nonsense', 123]

            mock_first_text.return_value = 'orchestrator reply'

            # Configure context
            context = {
                'message_history': [{'role': "assistant", 'content': "Hi"},
                                    {'role': "user", 'content': "Hello"}],
                'pos_context': {'message_history': []},
                'conversation_id': '123',
                'scenario_prompt': '',
                'customer_profile': {'prompt': 'customer prompt'}
            }
            expected_context = deepcopy(context)

            # Run test
            harness = PromptOrchestratorHarness()
            reply = harness.get_reply(context=context)

            # Context should not change
            self.assertEqual(context, expected_context)

            # reply should be the mock response from get_first_text_ai_response
            self.assertEqual(reply, 'orchestrator reply')

    def test_get_reply_none_type_return_from_orchestrator(self):
        with patch(
                'src.orchestrator.Orchestrator') \
                as MockOrchestrator, patch(
                'eval.library.conversation_generator.pos_harness.get_first_text_ai_response') \
                as mock_first_text:

            # Configure the mock behavior
            instance = MockOrchestrator.return_value
            instance.get_reply.return_value = None

            mock_first_text.return_value = 'orchestrator reply'

            # Configure context
            context = {
                'message_history': [{'role': "assistant", 'content': "Hi"},
                                    {'role': "user", 'content': "Hello"}],
                'pos_context': {'message_history': []},
                'conversation_id': '123',
                'scenario_prompt': '',
                'customer_profile': {'prompt': 'customer prompt'}
            }

            # Run test
            harness = PromptOrchestratorHarness()
            with self.assertRaises(ValueError):
                harness.get_reply(context=context)
