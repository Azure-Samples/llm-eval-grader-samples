from agents.weather.weather_assistant import WeatherAssistant
from agents.weather.weather_query_extractor import WeatherQueryExtractor
from context import Context


class WeatherAgent:
    """Answers weather questions."""

    def invoke(self, context: Context) -> str:
        extractor = WeatherQueryExtractor()

        query = extractor.extract(context)

        # invoke weather api

        assistant = WeatherAssistant()
        reply = assistant.invoke(context)

        return reply
