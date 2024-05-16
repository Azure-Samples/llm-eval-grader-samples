from agents.location.location_assistant import LocationAssistant
from agents.location.location_extractor import LocationExtractor
from context import Context


class LocationAgent:
    """Identifies user's location."""

    def invoke(self, context: Context) -> str | None:
        extractor = LocationExtractor()

        extractor.extract(context)

        if context.location is not None:
            return None

        assistant = LocationAssistant()
        reply = assistant.invoke(context.get_messages())

        return reply
