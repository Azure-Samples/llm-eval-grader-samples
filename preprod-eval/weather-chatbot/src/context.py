from src.clients.weather import WeatherType


class Context:
    """Holds the conversation context."""
    def __init__(self):
        self._messages = []
        self._location: tuple[float, float] | None = None
        self._location_description: str | None = None
        self._weather_category: WeatherType | None = None

    def add_message(self, role: str, message: str):
        self._messages += [{"role": role, "content": message}]

    def get_messages(self):
        return self._messages

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value: tuple[float, float]):
        self._location = value

    @property
    def location_description(self):
        return self._location_description

    @location_description.setter
    def location_description(self, value: str):
        self._location_description = value

    @property
    def weather_category(self):
        return self._weather_category

    @weather_category.setter
    def weather_category(self, value: str):
        self._weather_category = value
