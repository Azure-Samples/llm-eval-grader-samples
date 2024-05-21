from context import Context


class WeatherAssistant:
    """Class for answering weather questions."""
    def invoke(self, context: Context) -> str:
        # message_history = context.get_messages()

        return "weather assistant done (stub)"
        # return f"stub for answering weather questions for {context.location_description}"
