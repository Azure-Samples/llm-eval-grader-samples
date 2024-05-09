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
            api_key=os.getenv("OPENAI_API_KEY"),
            azure_endpoint=os.getenv("OPENAI_API_BASE"),
            api_version=os.getenv("OPENAI_API_VERSION")
        )
        self.max_retry = os.getenv("MAX_RETRY_COUNT")
        self.deployment_name = os.getenv("OPENAI_DEPLOYMENT_NAME")
        
    def get_completion(self, messages, temperature, max_tokens: Optional[int] = None):
        """This method generates a response from the Azure OpenAI API

        Args:
            messages: message to send to the Azure OpenAI API
            temperature: maximum number of tokens to generate
            max_tokens (Optional[int], optional): temperature parameter for sampling. Defaults to None.
        """
        last_exception = Exception("Invalid state")
        for i in range(int(self.max_retry)):
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
                print(f"AttributeError, attempt {i + 1}")
            except RateLimitError as e:
                last_exception = e
                print(f"RateLimitError, attempt {i + 1}")
                if i != self.max_retry - 1:
                    sleep(6)
            except (Timeout, ReadTimeoutError, APIConnectionError) as e:
                last_exception = e
                e_name = e.__class__.__name__
                print(f"{e_name}, attempt {i + 1}")

        raise last_exception

chat_completion = ChatCompletion()
