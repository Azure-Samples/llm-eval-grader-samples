import inspect
from openai import AzureOpenAI
import os

from src.clients.weather import Weather, WeatherType
from src.context import Context


class WeatherAssistant:
    """Class for answering weather questions."""
    def invoke(self, context: Context) -> str:

        message_history = context.get_messages()

        if len(message_history) == 0:
            return

        weather_data = None

        if context.weather_category:
            weather_client = Weather()
            weather_data = weather_client.\
                get_weather(lat=context.location[0], lon=context.location[1], weather_type=context.weather_category)

        flattened_history = "\n".join([f"{m['role']}: {m['content']}" for m in message_history])

        weather_data_suffix = ''

        if context.weather_category:
            weather_data_suffix = ', ' + context.weather_category.name.replace('_', ' ').lower()

        system_prompt = inspect.cleandoc(f"""
            Your task is to try and determine what a user wants to know about the weather and
            try to answer their questions. Use the following json formatted weather data and conversation transcript
            to figure out what their questions are and answer them. You do not need to ask for their location.

            If the weather data is None or they haven't  asked a question yet, ask the user what category of
            weather they would like to know about from the following
            choices: {[enum.name.replace('_', ' ').lower() for enum in WeatherType]}.
            Getting this information will help us to choose the correct weather data. If you've answered a
            question ask them if they have any more.

            Weather data{weather_data_suffix}:
            ```
            {weather_data}
            ```

            Conversation transcript:
            ```
            {flattened_history}
            ```
            """)

        messages = [{"role": "system", "content": system_prompt}]

        response = AzureOpenAI().chat.completions.create(
            temperature=0,
            model=os.environ["OPENAI_DEPLOYMENT_NAME"],
            messages=messages)

        response = response.choices[0].message.content

        return response
