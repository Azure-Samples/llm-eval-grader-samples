import unittest
from unittest.mock import patch
from eval.library.conversation_generator.user_generation.standard_user import StandardUserGenerator

user_profiles = [
    {
        "name": "Alex",
        "location": "You live in Calgary, Alberta. ",
        "personality": "You ask probing, technical questions.  You ask follow-up questions whenever the answer is complicated, to make sure you fully understand.",
        "other": "none",
        "attribute_dict": {
            "location": {"city": "Calgary", "state": "Alberta"}
        }
    }
]

class TestStandardUserGenerator(unittest.TestCase):
    def _path_to_module_as_string(self):
        return "eval.library.conversation_generator.user_generation.standard_user"

    def test_standard_user(self):
        with patch(f'{self._path_to_module_as_string()}.StandardUserGenerator._load_user_profiles') \
                as mock_load_user_profiles:
            def set_mock_value(instance):
                instance.user_profiles = user_profiles

            # Mock load of profiles from disk
            mock_load_user_profiles.return_value = None
            mock_load_user_profiles.side_effect = set_mock_value.__get__(StandardUserGenerator)

            # Validate that mocked profiles are loaded correctly and not modified in __init__
            user_gen = StandardUserGenerator()
            self.assertEqual(mock_load_user_profiles.call_count, 1)
            self.assertEqual(user_gen.user_profiles, user_profiles)

            # Validate format of user_profiles
            self.assertEqual(len(user_gen.valid_profiles), len(user_profiles))
            profile = user_gen.valid_profiles[0]
            self.assertIn('prompt', profile)
            self.assertIn('attributes', profile)
            self.assertIn('name', profile)

            # Check that we can cycle through profiles
            profile_1 = user_gen.generate_customer_profile()
            profile_2 = user_gen.generate_customer_profile()
            profile_3 = user_gen.generate_customer_profile()

            self.assertEqual(profile_1, profile_3)
            self.assertNotEqual(profile_1, profile_2)
