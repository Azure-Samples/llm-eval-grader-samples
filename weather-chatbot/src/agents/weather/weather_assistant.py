from src.context import Context


class WeatherAssistant:
    """Class for answering weather questions."""
    def invoke(self, context: Context) -> str:
        # message_history = context.get_messages()

        return "it's 75 degree and cloudy right now. the forcast tomorrow is highs of 76 and lows of 65 and it will be sunny (stub)"
