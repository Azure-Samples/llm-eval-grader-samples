from eval.library.inner_loop.mlflow_helpers.core.component_base_class import (
    ComponentWrapper
)
from src.agents.weather.prompts import WEATHER_ASSISTANT_BASE_PROMPT
from src.agents.weather.weather_assistant import WeatherAssistant
from eval.library.utils.inner_loop_helpers import EvaluationUtils


class WeatherAssistantComponent(ComponentWrapper):
    """Component wrapper for the Weather Assistant
    """
    def predict(self, context, component_input: dict) -> str | None:
        """
        This method contains the code required to instantiate the component with a variant and get a completion.

        There will be small differences for each component.
        """

        weather_assistant = WeatherAssistant()
        assistant_response = weather_assistant.invoke(message_history=component_input['context']['message_history'])

        return assistant_response

    def measure(self, parameters: dict) -> dict:
        """
        This method is used to evaluate completions from the component.

        It is called when an experiment runs.
        """
        component_input = parameters['component_input']
        
        return EvaluationUtils.evaluate_component_measure(component_input)

    def seed_prompt(self) -> dict:
        """
        Returns the seed prompt of component
        """
        seed_prompt = {
            'Weather_assistant_prompts': {
                "WEATHER_ASSISTANT_BASE_PROMPT": WEATHER_ASSISTANT_BASE_PROMPT
        }
        }

        return seed_prompt
