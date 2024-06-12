from eval.library.conversation_generator.assistantHarness import OrchestratorHarness

cfg = {
    "initial_assistant_message": "Hello!  How can I help you with the weather?",
    "scenario_prompt": "",
    "assistantHarness": OrchestratorHarness(),   # Expects .get_reply(context) api
    "log_location": 'logs/',
}
