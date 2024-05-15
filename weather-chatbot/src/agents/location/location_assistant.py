class LocationAssistant:
    """Class for asking user about their location."""
    def invoke(self, message_history: list[dict]) -> str:
        return "If you provide a street address, I can help you find the weather"
