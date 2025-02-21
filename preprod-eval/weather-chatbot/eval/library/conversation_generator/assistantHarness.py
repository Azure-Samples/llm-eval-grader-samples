# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from src.orchestrator import Orchestrator
from src.context import Context
from copy import deepcopy


class OrchestratorHarness:
    def __init__(self):
        self.orchestrator = Orchestrator()

    def get_reply(self, context: dict) -> str | None:

        # Get the latest user message
        messages = []
        message = context['message_history'][-1]['content']
        for _ in context['message_history']:
            cleaned_message = deepcopy(_)
            if 'context' in cleaned_message:
                del cleaned_message['context']
            messages.append(cleaned_message)
        assistantHarness_context = Context()
        assistantHarness_context._messages = messages

        reply = None
        reply = self.orchestrator.get_reply(user_message=message, context=assistantHarness_context)

        return reply
