from openai import AzureOpenAI
from dotenv import load_dotenv
from typing import Optional
import os


def get_completion(self, messages, temperature, max_tokens: Optional[int] = None):
    """This method generates a response from the Azure OpenAI API

    Args:
        messages: message to send to the Azure OpenAI API
        temperature: maximum number of tokens to generate
        max_tokens (Optional[int], optional): temperature parameter for sampling. Defaults to None.
    """
    load_dotenv()
    
    # Set the API key of azure openai
    client = AzureOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        azure_endpoint=os.environ["OPENAI_API_BASE"],
        api_version=os.environ["OPENAI_API_VERSION"]
    )
    deployment_name = os.environ["OPENAI_DEPLOYMENT_NAME"]

    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    completion = response.choices[0]

    content = completion.message.content
    return content