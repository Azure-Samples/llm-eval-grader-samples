# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import unittest
from unittest.mock import patch
from copy import deepcopy
from eval.library.conversation_generator.assistantHarness import OrchestratorHarness
import pytest
import json
import os


class TestAssistantHarness(unittest.TestCase):
    @pytest.fixture(scope='module', autouse=True)
    def setup(self):
        """ Set mock environment variables needed for each test """
        env_path = 'eval/tests/data/dummy_env.json'
        with open(env_path, 'r') as f_p:
            mock_variables = json.load(f_p)

        with patch.dict(os.environ, mock_variables):
            yield

    def test_get_reply(self):
        with patch(
                'eval.library.conversation_generator.assistantHarness.Orchestrator', autospec=True) \
                as MockOrchestrator:

            # Configure the mock behavior
            instance = MockOrchestrator.return_value
            instance.get_reply.return_value = 'orchestrator reply'

            # Configure context
            context = {
                'message_history': [{'role': "assistant", 'content': "Hi"},
                                    {'role': "user", 'content': "Hello"}],
                'assistantHarness_context': {'message_history': []},
                'conversation_id': '123',
                'scenario_prompt': '',
                'customer_profile': {'prompt': 'customer prompt'}
            }
            expected_context = deepcopy(context)

            # Run test
            harness = OrchestratorHarness()
            reply = harness.get_reply(context=context)

            # Context should not change
            self.assertEqual(context, expected_context)

            self.assertEqual(reply, 'orchestrator reply')

