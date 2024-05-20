from src.orchestrator import Orchestrator
import traceback
from src.models.models import AIRequestText, AIResponseText



class OrchestratorHarness:
    def __init__(self):
        self.orchestrator = Orchestrator()
        
    def get_first_text_ai_response(self, reply_list: list) -> str | None:
        text_reply = None
        for reply in reply_list:
            if isinstance(reply, AIResponseText):
                if text_reply is None:
                    text_reply = reply.responseContent
                else:
                    print(f'Received more than one AIResponseText elements {str(reply)}')
            else:
                print(f'ignoring assistant response until non-text responses are supported {str(reply)}')
        return text_reply

    def get_reply(self, context: dict) -> str | None:

        # Get the latest user message
        message = context['message_history'][-1]['content']

        reply = None
        try:
            reply_list = self.orchestrator.get_reply(user_message=AIRequestText(message), context=context['pos_context'])

            if reply_list is None:
                raise ValueError('BUGBUGBUG - Assistant did not return a response')

            reply = self.get_first_text_ai_response(reply_list)

        except Exception as e:
            print('---------------------------------------\nException occured. Please log a bug')
            print(traceback.format_exc())
            raise e

        return reply
