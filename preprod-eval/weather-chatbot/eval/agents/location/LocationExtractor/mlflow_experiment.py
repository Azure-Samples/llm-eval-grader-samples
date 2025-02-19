from src.agents.location.location_extractor import LocationExtractor
from eval.library.inner_loop.mlflow_helpers.core.agent_base_class import AgentWrapper
from eval.library.inner_loop.mlflow_helpers.eval.calculate_grade import exact_match_score
from azure.maps.search import MapsSearchClient
from azure.core.credentials import AzureKeyCredential
import os
from src.context import Context


class LocationExtractorAgent(AgentWrapper):
    """
    Agent wrapper for location Extractor
    """
    def predict(self, context, agent_input: dict) -> dict:
        """
        This method contains the code required to instantiate the agent with a variant and get a completion.

        There will be small differences for each agent.
        """
        messages = agent_input['context']

        # invoke extractor
        location = LocationExtractor()
        context = Context()
        context._messages = messages['message_history']
        location.extract(context=context)
        
        return context.location

    def measure(self, parameters: dict) -> dict:
        """
        This method is used to evaluate completions from the agent.

        It is called when an experiment runs.
        """
        credential = AzureKeyCredential(os.environ['MAPS_API_KEY'])
        search_client = MapsSearchClient(credential=credential)
        expected_output = parameters['attributes']['location']
        expected_output = f"{expected_output['city']}, {expected_output['state']}"
        search_results = search_client.search_address(expected_output)
        expected_results = [result for result in search_results.results if result.score > 0.7]
        expected_location = (expected_results[0].position.lat, expected_results[0].position.lon)
        actual_location = parameters['result']
        score = {}
        score['exact_match'] = exact_match_score(expected_output=expected_location, result=actual_location)

        return score


    def seed_prompt(self) -> dict:
        """
        Returns the seed prompt of agent
        """
        seed_prompt = {'location_extractor_seed_prompt': "dummy"}

        return seed_prompt