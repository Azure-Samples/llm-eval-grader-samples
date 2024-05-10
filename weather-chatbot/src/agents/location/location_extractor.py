import os
from azure.core.credentials import AzureKeyCredential
from azure.maps.search import MapsSearchClient
from dotenv import load_dotenv


class LocationExtractor:
    """Class for extracting location information from message history."""
    def __init__(self):
        """Initialize the search client for looking up the address of the latest message"""
        load_dotenv()
        credential = AzureKeyCredential(os.environ["AZURE_SUBSCRIPTION_KEY"])

        self.search_client = MapsSearchClient(
            credential=credential,
        )

    def extract(self, message_history: list[dict]) -> str | None:
        last_message = self.get_last_user_message(message_history)

        if last_message is not None:
            search_results = self.search_client.search_address(last_message['content'])

            # If we got results back from address lookups in the API, use the first one
            point_addresses = [result for result in search_results.results if result.type == 'Point Address']
            if len(point_addresses) > 0:
                return f'{point_addresses[0].position.lat} {point_addresses[0].position.lon}'
            
        return None
    
    def get_last_user_message(self, message_history: list[dict]):
        user_messages = [msg for msg in message_history if msg['role'] == 'user']
        message_count = len(user_messages)
        if message_count > 0:
            return user_messages[message_count - 1]
        
        return None

