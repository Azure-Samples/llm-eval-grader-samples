from src.orchestrator import Orchestrator
from src.context import Context


class OrchestratorHarness:
    def __init__(self):
        self.orchestrator = Orchestrator()

    def get_reply(self, context: dict) -> str | None:

        # Get the latest user message
        message = context['message_history'][-1]['content']
        pos_context = Context()
        pos_context._messages = context['message_history']

        reply = None
        reply = self.orchestrator.get_reply(user_message=message, context=pos_context)

        return reply
