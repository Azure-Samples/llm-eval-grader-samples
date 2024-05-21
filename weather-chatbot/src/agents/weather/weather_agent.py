from src.agents.weather.weather_assistant import WeatherAssistant
from src.agents.weather.weather_query_extractor import WeatherQueryExtractor
from src.context import Context


class WeatherAgent:
    """Answers weather questions."""

    def invoke(self, context: Context) -> str:
        extractor = WeatherQueryExtractor()

        query = extractor.extract(context)

        # invoke weather api

        assistant = WeatherAssistant()
        reply = assistant.invoke(context)

        return reply
