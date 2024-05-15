from agents.location.location_agent import LocationAgent
from agents.weather.weather_agent import WeatherAgent
from context import Context


class Orchestrator:
    """Drives the conversation flow."""

    def get_reply(self, user_message: str, context: Context) -> str:
        if user_message:
            context.add_message("user", user_message)

        if context.location is None:
            location_agent = LocationAgent()
            reply = location_agent.invoke(context)

        if context.location is not None:
            weather_agent = WeatherAgent()
            reply = weather_agent.invoke(context)

        context.add_message("assistant", reply)

        return reply
