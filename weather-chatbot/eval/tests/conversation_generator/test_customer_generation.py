import unittest
from unittest.mock import patch
from eval.library.conversation_generator.user_generation.random_user import RandomUserGenerator
from eval.library.conversation_generator.user_generation.standard_user import StandardUserGenerator

user_profiles = [
    {
        "name": "Arcana",
        "vehicle_or_tire_size": "vehicle",
        "location": "You live in Laval, Quebec.",
        "tire_preferences": "When it comes to tires",
        "tire_season": "You will use these tires in the winter",
        "vehicle_instructions": "You drive a 2019 Toyota Highlander",
        "personality": "You give short and concise responses.",
        "inventory": "To get the right tires, you'd be willing to drive up to 15 minutes from your home.",
        "other": "If the assistant makes you repeat yourself you will get frustrated.",
        "attribute_dict": {"vehicle": {"year": 2019, "brand": "Toyota", "model": "Highlander",
                                       "body": "4 Dr Sport Utility", "option": "XLE 19\" option"}}
    },
    {
        "name": "Stylor",
        "vehicle_or_tire_size": "vehicle",
        "location": "You live in northern BC.  You enjoy back woods activities like boating and camping.",
        "tire_preferences": "When it comes to tires, you want longevity and good grip in muddy and sandy conditions.",
        "tire_season": "You will use these tires in 3 seasons (spring, summer, fall). ",
        "vehicle_instructions": "You drive a Ram 2500 made in 2018, the trim is SLT.",
        "personality": "You give brief, informal responses and make spelling and grammar mistakes.",
        "inventory": "You want to be able to pick up your new tires in the store closest to you.",
        "other": "never end the conversation.",
        "attribute_dict": {"vehicle": {"year": 2018, "brand": "Ram", "model": "2500",
                                       "body": "2 Dr Standard Cab Pickup, 8 Ft Bed", "option": "SLT 20\" option"}}
    }
]


class TestRandomUserGenerator(unittest.TestCase):
    def setUp(self):
        self.customer_generator = RandomUserGenerator()
        self.module_path = 'eval.library.conversation_generator.user_generation.random_user.RandomUserGenerator'  # noqa: E501
    
    def test_generate_customer_profile(self):
        with patch('secrets.choice') as mock_secrets_choice, \
             patch(f'{self.module_path}._weighted_random_choice') as mock_weighted_choice, \
             patch(f'{self.module_path}._select_year_for_brand') as mock_select_year:

            # Mocking secrets.choice and random.sample with predetermined values
            mock_secrets_choice.side_effect = lambda x: x[0]
            mock_weighted_choice.return_value = 'Hyundai'
            mock_select_year.return_value = '2018'

            profile = self.customer_generator.generate_customer_profile()
            self.assertIn('prompt', profile)
            self.assertIn('attributes', profile)
            self.assertIn('name', profile)

            # Verifying that the mocked methods were called
            mock_secrets_choice.assert_called()
            mock_weighted_choice.assert_called()
            mock_select_year.assert_called()

        second_profile = self.customer_generator.generate_customer_profile()
        self.assertNotEqual(profile, second_profile)
    
    def test_weighted_random_choice(self):
        items = ['item1', 'item2', 'item3']
        weights = [0.1, 0.3, 0.6]
        scale_factor = 1000  
        scaled_weights = [int(weight * scale_factor) for weight in weights]
        cum_weights = [sum(scaled_weights[:i + 1]) for i in range(len(scaled_weights))]

        with patch('secrets.randbelow') as mock_randbelow:
            for i in range(len(items)):
                # Set randbelow to return a value within the range for each item
                if i == 0:
                    mock_randbelow.return_value = 0
                else:
                    mock_randbelow.return_value = cum_weights[i - 1]

                result = self.customer_generator._weighted_random_choice(items, weights)
                self.assertEqual(result, items[i])

    def test_extract_brands(self):
        mock_vehicles = ['2020 Toyota Camry', '2019 Honda Accord']
        expected_brands = ['Toyota', 'Honda']
        brands = self.customer_generator._extract_brands(mock_vehicles)
        self.assertEqual(brands, expected_brands)
    
    def test_get_vehicles_by_brand(self):
        brand = 'Toyota'
        vehicles = self.customer_generator._get_vehicles_by_brand(brand)
        for vehicle in vehicles:
            self.assertIn(brand, vehicle)

    def test_get_unique_years_for_brand(self):
        brand_vehicles = ['2020 Toyota Camry', 'Toyota 2019 Corolla', '2021 Toyota RAV4']
        unique_years = self.customer_generator._get_unique_years_for_brand(brand_vehicles)
        self.assertIn('2020', unique_years)
        self.assertIn('2019', unique_years)
        self.assertIn('2021', unique_years)

    def test_select_year_for_brand(self):
        brand = 'Toyota'
        with patch(f'{self.module_path}._weighted_random_choice') as mock_weighted_choice:
            mock_weighted_choice.return_value = '2020'
            selected_year = self.customer_generator._select_year_for_brand(brand)
            self.assertEqual(selected_year, '2020')


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
