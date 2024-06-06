from src.agents.weather.weather_extractor import WeatherExtractor
from eval.library.inner_loop.mlflow_helpers.core.component_base_class import ComponentWrapper
from eval.library.inner_loop.mlflow_helpers.eval.calculate_grade import exact_match_score
import os
from src.context import Context


class WeatherExtractorComponent(ComponentWrapper):
    """
    Component wrapper for location Extractor
    """
    def predict(self, context, component_input: dict) -> dict:
        """
        This method contains the code required to instantiate the component with a variant and get a completion.

        There will be small differences for each component.
        """
        messages = component_input['context']

        # invoke extractor
        weather = WeatherExtractor()
        context = Context()
        context._messages = messages['message_history']
        weather.extract(context=context)
        
        return context.weather_category.name

    def measure(self, parameters: dict) -> dict:
        """
        This method is used to evaluate completions from the component.

        It is called when an experiment runs.
        """
        expected_weather_cat = parameters['attributes']['weather_category']
        actual_weather_cat = parameters['result']
        score = {}
        score['exact_match'] = exact_match_score(expected_output=expected_weather_cat, result=actual_weather_cat)

        return score


    def seed_prompt(self) -> dict:
        """
        Returns the seed prompt of component
        """
        seed_prompt = {'location_extractor_seed_prompt': "dummy"}

        return seed_prompt