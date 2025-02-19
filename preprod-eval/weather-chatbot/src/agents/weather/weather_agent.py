from src.agents.weather.weather_assistant import WeatherAssistant
from src.agents.weather.weather_extractor import WeatherExtractor
from src.context import Context


class WeatherAgent:
    """Answers weather questions."""

    def invoke(self, context: Context) -> str:

        extractor = WeatherExtractor()

        extractor.extract(context)

        assistant = WeatherAssistant()
        reply = assistant.invoke(context)

        return reply
