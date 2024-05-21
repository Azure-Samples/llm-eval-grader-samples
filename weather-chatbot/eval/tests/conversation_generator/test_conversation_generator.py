import unittest
from unittest.mock import patch
import io
import sys

from eval.library.conversation_generator.conversation import ConversationGenerator


class MockAzureChatOpenAIResponse:
    def __init__(self):
        self.content = 'customer reply'


class TestConversationGenerator(unittest.TestCase):
    def test_initialize_context_with_assistant_message(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as OrchestratorHarness:

            # Set mock return values
            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'

            assistantHarness = OrchestratorHarness.return_value
            assistantHarness.get_reply.return_value = 'assistant reply'

            # Prepare data
            context = {'message_history': [{'role': 'assistant', 'content': 'first assistant message'}]}
            scenario_prompt = "scenario prompt"
            customer_profile = {'prompt': 'profile prompt', 'attributes': {}}

            # Invoke the method under test
            cg = ConversationGenerator()
            new_context = cg.initialize_context(context, scenario_prompt, customer_profile)

            # Verify that the context matches expectations
            self.assertEqual(new_context['scenario_prompt'], 'scenario prompt')
            self.assertEqual(new_context['message_history'], [
                {'role': 'assistant', 'content': 'first assistant message'},
                {'role': 'user', 'content': 'customer reply'}])
            self.assertIn('conversation_id', new_context)
            self.assertEqual(new_context['assistantHarness_context'], {'message_history': []})

            # Verify call counts
            self.assertEqual(assistantHarness.get_reply.call_count, 0)
            self.assertEqual(cc.get_reply.call_count, 1)

    def test_initialize_context_with_both_messages(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as OrchestratorHarness:

            # Set mock return values
            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'

            assistantHarness = OrchestratorHarness.return_value
            assistantHarness.get_reply.return_value = 'assistant reply'

            # Prepare data
            context = {'message_history': [{'role': 'assistant', 'content': 'first assistant message'},
                                           {'role': 'user', 'content': 'the sky is blue'}]}
            scenario_prompt = "scenario prompt"
            customer_profile = {'prompt': 'profile prompt', 'attributes': {}}

            # Invoke the method under test
            cg = ConversationGenerator()
            new_context = cg.initialize_context(context, scenario_prompt, customer_profile)

            # Verify that the context is as expected
            self.assertEqual(new_context['scenario_prompt'], 'scenario prompt')
            self.assertEqual(new_context['message_history'], [
                {'role': 'assistant', 'content': 'first assistant message'},
                {'role': 'user', 'content': 'the sky is blue'}])
            self.assertIn('conversation_id', new_context)
            self.assertEqual(new_context['assistantHarness_context'], {'message_history': []})

            # Verify call counts
            self.assertEqual(assistantHarness.get_reply.call_count, 0)
            self.assertEqual(cc.get_reply.call_count, 0)

    def test_generate_turn(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as OrchestratorHarness, patch(
                f'{module_path}.generate_turn') as mock_generate_turn:

            # Set mock return values
            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'

            assistantHarness = OrchestratorHarness.return_value
            assistantHarness.get_reply.return_value = 'assistant reply'

            mock_generate_turn.return_value = {}

            # Verify that cg.generate_turn() invokes the imported generate_turn once
            context = {}
            cg = ConversationGenerator()
            cg.generate_turn(context)
            self.assertEqual(mock_generate_turn.call_count, 1)
            self.assertEqual(context, {})

    def test_generate_test_case_single_turn(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as OrchestratorHarness, patch(
                f'{module_path}.ConversationGenerator.initialize_context') as mock_initialize_context, patch(
                f'{module_path}.ConversationGenerator.generate_turn') as mock_generate_turn, patch(
                f'{module_path}.ConversationGenerator.test_case_interrupter') as mock_test_case_interrupter, patch(
                f'{module_path}.ConversationGenerator.conversation_interrupter') as mock_conversation_interrupter:

            # Set mock responses
            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'
            assistantHarness = OrchestratorHarness.return_value
            assistantHarness.get_reply.return_value = 'assistant reply'
            mock_initialize_context.return_value = {}
            mock_generate_turn.return_value = {}
            mock_test_case_interrupter.return_value = True
            mock_conversation_interrupter.return_value = False

            cg = ConversationGenerator()
            cg.generate_test_case(scenario_prompt="", customer_profile={}, end_of_test_case_key="")
            self.assertEqual(mock_generate_turn.call_count, 1)
            self.assertEqual(mock_initialize_context.call_count, 1)

    def test_generate_test_case_multiple_turns(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as OrchestratorHarness, patch(
                f'{module_path}.ConversationGenerator.initialize_context') as mock_initialize_context, patch(
                f'{module_path}.ConversationGenerator.generate_turn') as mock_generate_turn, patch(
                f'{module_path}.ConversationGenerator.test_case_interrupter') as mock_test_case_interrupter, patch(
                f'{module_path}.ConversationGenerator.conversation_interrupter') as mock_conversation_interrupter:

            # Set mock responses
            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'
            assistantHarness = OrchestratorHarness.return_value
            assistantHarness.get_reply.return_value = 'assistant reply'
            mock_initialize_context.return_value = {}
            mock_generate_turn.return_value = {}
            mock_test_case_interrupter.return_value = False
            mock_conversation_interrupter.return_value = False

            cg = ConversationGenerator(max_turns=5)
            cg.generate_test_case(scenario_prompt="", customer_profile={}, end_of_test_case_key="")
            self.assertEqual(mock_generate_turn.call_count, 4)
            self.assertEqual(mock_initialize_context.call_count, 1)
            self.assertEqual(mock_test_case_interrupter.call_count, 4)

    def test_generate_conversation(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as OrchestratorHarness, patch(
                f'{module_path}.ConversationGenerator.initialize_context') as mock_initialize_context, patch(
                f'{module_path}.ConversationGenerator.generate_turn') as mock_generate_turn, patch(
                f'{module_path}.ConversationGenerator.conversation_interrupter') as mock_interrupter:

            # Set mock responses
            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'
            assistantHarness = OrchestratorHarness.return_value
            assistantHarness.get_reply.return_value = 'assistant reply'
            mock_initialize_context.return_value = {}
            mock_generate_turn.return_value = {}
            mock_interrupter.return_value = False

            cg = ConversationGenerator(max_turns=2)
            cg.generate_conversation(customer_profile={}, scenario_prompt="")
            self.assertEqual(mock_initialize_context.call_count, 1)
            self.assertEqual(mock_generate_turn.call_count, 1)
            self.assertEqual(mock_interrupter.call_count, 1)

    def test_print_conversation(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as OrchestratorHarness:

            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'

            assistantHarness = OrchestratorHarness.return_value
            assistantHarness.get_reply.return_value = 'assistant reply'

            cg = ConversationGenerator()
            context = {
                'conversation_id': 'abc123',
                'message_history': [{'role': 'assistant', 'content': 'hello world'}]}

            # Run test
            captured_output = io.StringIO()
            sys.stdout = captured_output
            cg.print_conversation(context=context, print_conversation_id=False)

            self.assertGreater(len(captured_output.getvalue()), 0)

            # Check that printing conversation_id works, too
            captured_output_2 = io.StringIO()
            sys.stdout = captured_output_2
            cg.print_conversation(context=context, print_conversation_id=True)

            self.assertGreater(len(captured_output_2.getvalue()), len(captured_output.getvalue()))

            # Restore printing to normal
            sys.stdout = sys.__stdout__
