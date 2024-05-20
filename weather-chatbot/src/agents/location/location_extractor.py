import os
from azure.core.credentials import AzureKeyCredential
from azure.maps.search import MapsSearchClient
from openai import AzureOpenAI
from location_prompt import location_extractor_prompt

from context import Context


geo_score_threshold = 0.7
location_unknown = "LOCATION UNKNOWN"

HISTORY_REPLACE_STRING = "{message_history}"

class LocationExtractor:
    """Class for extracting location information from message history."""
    def __init__(self):
        """Initialize the search client for looking up the address of the latest message"""
        credential = AzureKeyCredential(os.environ["MAPS_API_KEY"])

        self.search_client = MapsSearchClient(credential=credential)

    def extract(self, context: Context):
        message_history = context.get_messages()
        if len(message_history) == 0:
            return None

        history = "\n".join([f"{m['role']}: {m['content']}" for m in message_history])
        system_prompt = location_extractor_prompt.replace(HISTORY_REPLACE_STRING, history)

        messages = [{"role": "system", "content": system_prompt}]

        response = AzureOpenAI().chat.completions.create(
            temperature=0,
            model=os.environ["OPENAI_DEPLOYMENT_NAME"],
            messages=messages)

        location_description = response.choices[0].message.content or ""

        if location_unknown in location_description.upper():
            return

        search_results = self.search_client.search_address(location_description)

        results = [result for result in search_results.results if result.score > geo_score_threshold]

        if len(results) > 0:
            context.location = (results[0].position.lat, results[0].position.lon)
            context.location_description = f"{results[0].address.country}, {results[0].address.freeform_address}"
