from unittest import TestCase
from unittest.mock import patch

from eval.library.utils.eval_helpers import get_conversation_as_string


class TestEvalDataHelpersObject(TestCase):

    def test_get_conversation_as_string(self):
        module_path = 'eval.library.conversation_generator.conversation'
        with patch(f'{module_path}.CustomerChat') as CustomerChat, patch(
                f'{module_path}.OrchestratorHarness') as PromptOrchestratorHarness:

            cc = CustomerChat.return_value
            cc.get_reply.return_value = 'customer reply'
            pos = PromptOrchestratorHarness.return_value
            pos.get_reply.return_value = 'assistant reply'

            context = {
                'conversation_id': 'abc123',
                'message_history': [{'role': 'assistant', 'content': 'hello world'}]}
            conversation_string = get_conversation_as_string(context=context)

            self.assertGreater(len(conversation_string), 0)
