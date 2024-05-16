"""Generate prompts that specify the traits of unique customers.  This will create diverse emulated users.

You can run this file to see some generated customers.
TODO: Add attributes once they are figured out"""

from eval.library.conversation_generator.templates.customer_profile_template import (
    customer_profile_template)
import secrets


class RandomUserGenerator:
    """Generate unique customer profiles"""
    def __init__(self):
        base_path = 'eval/library/conversation_generator/customer_profile_data'
        self.places = self._read_data_file(path=f'{base_path}/places.txt')
        self.personalities = self._read_data_file(path=f'{base_path}/personality.txt')

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


        profile = {
            'prompt': customer_profile_template.replace("{place}", place).replace(
                                                       "{personality}", personality),
            'attributes': {'location': location_attribute},
            'name': 'randomly generated user'
        }

        return profile
