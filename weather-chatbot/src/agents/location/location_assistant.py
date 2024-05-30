from openai import AzureOpenAI
import os


class LocationAssistant:
    """Class for asking user about their location."""
    def invoke(self, message_history: list[dict]) -> str:

        system_prompt = """\
You are a chatbot that can answer questions about weather at a location provided by the user.
Talk to the user and ask them to provide their geographical location.
Make sure that the user specified country and city. zip code is optional but useful.
Sometimes state or province is also needed.
To answer the questions you need to know the user's location first but
the user has not provided the required information yet. Ask the user to provide missing information.
You can use only what the user has provided in the chat.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }] + message_history

        response = AzureOpenAI().chat.completions.create(
            temperature=0,
            model=os.environ["OPENAI_DEPLOYMENT_NAME"],
            messages=messages)

        result = response.choices[0].message.content

        return result
