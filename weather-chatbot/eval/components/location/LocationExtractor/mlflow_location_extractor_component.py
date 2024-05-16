from src.agents.location.location_extractor import LocationExtractor
from src.agents.location.location_assistant import LocationAssistant
from eval.library.utils import aml_utils 
from eval.library.inner_loop.component_base_class import ComponentWrapper
from eval.library.inner_loop.mlflow_helpers import is_value_in_list


class LocationAssistantComponent(ComponentWrapper):
    """
    Component wrapper for location Extractor
    """
    def predict(self, context, component_input: dict) -> dict:
        """
        This method contains the code required to instantiate the component with a variant and get a completion.

        There will be small differences for each component.
        """
        context = component_input['context']

        # invoke extractor
        location = LocationExtractor()
        location_extracted = location.extract(context=context)
        
        return location_extracted


    def measure(self, parameters: dict) -> dict:
        """
        This method is used to evaluate completions from the component.

        It is called when an experiment runs.
        """
        expected_output = parameters['expected_output']
        result = parameters['result']
        score = {}
        score['exact_match'] = is_value_in_list(expected_output=expected_output, result=result)

        return score


    def seed_prompt(self) -> dict:
        """
        Returns the seed prompt of component
        """
        seed_prompt = {'change_detection_assistant_seed_prompt': LocationAssistant.PROMPT_TEMPLATE}

        return seed_prompt
