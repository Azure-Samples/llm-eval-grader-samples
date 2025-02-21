# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from eval.library.inner_loop.mlflow_helpers.core.agent_base_class import (
    AgentWrapper
)
from src.agents.location.prompts import LOCATION_ASSISTANT_BASE_PROMPT
from src.agents.location.location_assistant import LocationAssistant
from eval.library.utils.inner_loop_helpers import EvaluationUtils


class LocationAssistantAgent(AgentWrapper):
    """Agent wrapper for the Location Assistant
    """
    def predict(self, context, agent_input: dict) -> str | None:
        """
        This method contains the code required to instantiate the agent with a variant and get a completion.

        There will be small differences for each agent.
        """

        location_assistant = LocationAssistant()
        assistant_response = location_assistant.invoke(message_history=agent_input['context']['message_history'])

        return assistant_response

    def measure(self, parameters: dict) -> dict:
        """
        This method is used to evaluate completions from the agent.

        It is called when an experiment runs.
        """
        agent_input = parameters['agent_input']
        
        return EvaluationUtils.evaluate_agent_measure(agent_input)

    def seed_prompt(self) -> dict:
        """
        Returns the seed prompt of agent
        """
        seed_prompt = {
            'location_assistant_prompts': {
                "LOCATION_ASSISTANT_BASE_PROMPT": LOCATION_ASSISTANT_BASE_PROMPT
        }
        }

        return seed_prompt
