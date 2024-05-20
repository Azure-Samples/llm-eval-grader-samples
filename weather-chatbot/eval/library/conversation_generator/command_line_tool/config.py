from eval.library.conversation_generator.pos_harness import OrchestratorHarness

cfg = {
    "initial_assistant_message": "Hello!  How can I help you with the weather?",
    "scenario_prompt": "",
    "pos": OrchestratorHarness(),   # Expects .get_reply(context) api
    "log_location": 'logs/',
}
