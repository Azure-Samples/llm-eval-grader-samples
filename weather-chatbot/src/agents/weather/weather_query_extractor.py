from context import Context


class WeatherQueryExtractor:
    """Class for extracting weather request from the context."""
    def extract(self,  context: Context) -> str | None:
        message_history = context.get_messages()
        return None
