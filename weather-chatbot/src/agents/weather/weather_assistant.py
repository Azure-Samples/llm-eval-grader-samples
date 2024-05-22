from src.context import Context
from src.clients.weather import Weather, WeatherType


class WeatherAssistant:
    """Class for answering weather questions."""
    def invoke(self, context: Context) -> str:
        message_history = context.get_messages()

        weather_data = None

        if context.weather_category:
            weather_client = Weather()
            weather_data = weather_client.get_weather(lat=context.location[0], lon=context.location[1], weather_type=context.weather_category)



        return "weather assistant done (stub)"
