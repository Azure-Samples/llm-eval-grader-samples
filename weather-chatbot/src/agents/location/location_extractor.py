first_call = True  # used only for the stub implementation


class LocationExtractor:
    """Class for extracting location information from message history."""
    def extract(self, message_history: list[dict]) -> str | None:
        global first_call  # used only for the stub implementation
        result = None if first_call else "98144"
        first_call = False
        return result
