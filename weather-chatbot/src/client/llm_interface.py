from openai import AzureOpenAI
from dotenv import load_dotenv
from typing import Optional
from openai import (
    RateLimitError,
    Timeout,
    APIConnectionError
)
from urllib3.exceptions import ReadTimeoutError
from time import sleep
import os


class ChatCompletion:
    def __init__(self):
        """Initialize the ChatCompletion wrapper."""
        load_dotenv()
        
        # Set the API key of azure openai
        self.client = AzureOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            azure_endpoint=os.environ["OPENAI_API_BASE"],
            api_version=os.environ["OPENAI_API_VERSION"]
        )
        self.deployment_name = os.getenv("OPENAI_DEPLOYMENT_NAME")
        
    def get_completion(self, messages, temperature, max_tokens: Optional[int] = None):
        """This method generates a response from the Azure OpenAI API

        Args:
            messages: message to send to the Azure OpenAI API
            temperature: maximum number of tokens to generate
            max_tokens (Optional[int], optional): temperature parameter for sampling. Defaults to None.
        """
        last_exception = Exception("Invalid state")
        try:
    
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            completion = response.choices[0]

            content = completion.message.content
            return content
    
        except AttributeError as e:
            last_exception = e
            print(f"AttributeError")
        except RateLimitError as e:
            last_exception = e
            print(f"RateLimitError")
        except (Timeout, ReadTimeoutError, APIConnectionError) as e:
            last_exception = e
            e_name = e.__class__.__name__
            print(f"{e_name}")

        raise last_exception
