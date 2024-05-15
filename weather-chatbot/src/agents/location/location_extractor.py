import os
from azure.core.credentials import AzureKeyCredential
from azure.maps.search import MapsSearchClient
from openai import AzureOpenAI


class LocationExtractor:
    """Class for extracting location information from message history."""
    def __init__(self):
        """Initialize the search client for looking up the address of the latest message"""
        credential = AzureKeyCredential(os.environ["AZURE_SUBSCRIPTION_KEY"])

        self.search_client = MapsSearchClient(credential=credential)

    def extract(self, message_history: list[dict]) -> str | None:
        if len(message_history) == 0:
            return None

        flattened_history = "\n".join([f"{m['role']}: {m['content']}" for m in message_history])

        system_prompt = f"""\
Your task is to extract location information from the conversation with the user.
Conversation transcript:
```
{flattened_history}
```

You need to know country, city, state or province, street address, and zip code.
If it is a well known city you can try to guess the country.
Analyze the conversation transcript carefully and extract the location information as a single line in the
name value pair format without any explanations.
"""

        messages = [{"role": "system", "content": system_prompt}]

        response = AzureOpenAI().chat.completions.create(
            model=os.environ["OPENAI_DEPLOYMENT_NAME"],
            messages=messages)

        location_description = response.choices[0].message.content

        search_results = self.search_client.search_address(location_description)

        point_addresses = [result for result in search_results.results if result.type == 'Point Address']
        if len(point_addresses) > 0:
            return f'{point_addresses[0].position.lat} {point_addresses[0].position.lon}'

        return None
