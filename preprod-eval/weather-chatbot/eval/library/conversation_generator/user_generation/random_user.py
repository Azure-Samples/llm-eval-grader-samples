"""Generate prompts that specify the traits of unique customers.  This will create diverse emulated users.

You can run this file to see some generated customers.
TODO: Add attributes once they are figured out"""

from eval.library.conversation_generator.templates.customer_profile_template import (
    customer_profile_template)
import secrets
import json
import os


class RandomUserGenerator:
    """Generate unique customer profiles"""
    def __init__(self):
        my_path = os.path.abspath(os.path.dirname(__file__))
        base_path = os.path.join(my_path, "../customer_profile_data")
        self.places = self._read_data_file(path=os.path.join(base_path, 'places.txt'))
        self.personalities = self._read_data_file(path=os.path.join(base_path, 'personality.txt'))
        self.weather_questions = self._read_data_file(path=os.path.join(base_path, 'weather_questions.txt'))

    def _read_data_file(self, path):
        r = []
        with open(path, "r") as f:
            for row in f:
                r.append(row.strip())
        return r
    

    def generate_customer_profile(self) -> dict:
        place = secrets.choice(self.places)
        location_attribute = {"city": place.split(", ")[0], "state": place.split(", ")[1]}
        personality = secrets.choice(self.personalities)
        weather_question_pair = secrets.choice(self.weather_questions).split(', ')
        weather_question = weather_question_pair[0]
        weather_category = json.loads(weather_question_pair[1])['weather_category']


        profile = {
            'prompt': customer_profile_template.replace("{place}", place).replace(
                                                       "{personality}", personality).replace(
                                                           "{weather_question}", weather_question),
            'attributes': {'location': location_attribute,
                           'weather_category': weather_category},
            'name': 'randomly generated user'
        }

        return profile
