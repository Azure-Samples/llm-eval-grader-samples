from eval.library.inner_loop.mlflow_helpers.core.component_base_class import (
    ComponentWrapper
)
from src.agents.location.prompts import LOCATION_ASSISTANT_BASE_PROMPT
from src.agents.location.location_assistant import LocationAssistant
from eval.library.utils.inner_loop_helpers import EvaluationUtils


class VehicleIdentifierComponent(ComponentWrapper):
    """Component wrapper for Vehicle Info Extractor
    """
    def predict(self, context, component_input: dict) -> str | None:
        """
        This method contains the code required to instantiate the component with a variant and get a completion.

        There will be small differences for each component.
        """

        location_assistant = LocationAssistant()
        assistant_response = location_assistant.invoke(context=component_input['context'])

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
            'location_assistant_prompts': {
                "LOCATION_ASSISTANT_BASE_PROMPT": LOCATION_ASSISTANT_BASE_PROMPT
        }
        }

        return seed_prompt
