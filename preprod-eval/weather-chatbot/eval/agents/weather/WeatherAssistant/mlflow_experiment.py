# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from eval.library.inner_loop.mlflow_helpers.core.agent_base_class import (
    AgentWrapper
)
from src.agents.weather.prompts import WEATHER_ASSISTANT_BASE_PROMPT
from src.agents.weather.weather_assistant import WeatherAssistant
from eval.library.utils.inner_loop_helpers import EvaluationUtils
from src.context import Context


class WeatherAssistantAgent(AgentWrapper):
    """Agent wrapper for the Weather Assistant
    """
    def predict(self, context, agent_input: dict) -> str | None:
        """
        This method contains the code required to instantiate the agent with a variant and get a completion.

        There will be small differences for each agent.
        """

        weather_assistant = WeatherAssistant()
        context = Context()
        context._messages = agent_input['context']['message_history']
        assistant_response = weather_assistant.invoke(context=context)

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
            'Weather_assistant_prompts': {
                "WEATHER_ASSISTANT_BASE_PROMPT": WEATHER_ASSISTANT_BASE_PROMPT
        }
        }

        return seed_prompt
