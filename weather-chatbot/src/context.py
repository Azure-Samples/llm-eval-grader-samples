class Context:
    """Holds the conversation context."""
    def __init__(self):
        self._messages = []
        self._location = None

    def add_message(self, role: str, message: str):
        self._messages += [[{"role": role, "content": message}]]

    def get_messages(self):
        return self._messages

    @property
    def location(self):
        return self._location
    
    @location.setter
    def location(self, value: str):
        self._location = value
