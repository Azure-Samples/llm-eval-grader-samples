from agents.location.location_agent import LocationAgent
from agents.weather.weather_agent import WeatherAgent
from context import Context


class Orchestrator:
    """Drives the conversation flow."""

    def get_reply(self, user_message: str | None, context: Context) -> str:
        if user_message:
            context.add_message("user", user_message)

        location_agent = LocationAgent()
        reply = location_agent.invoke(context)

        if reply is None:
            weather_agent = WeatherAgent()
            reply = weather_agent.invoke(context)

        context.add_message("assistant", reply)

        return reply
