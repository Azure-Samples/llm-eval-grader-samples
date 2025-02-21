# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from copy import deepcopy
from pathlib import Path
from eval.library.conversation_generator.templates.customer_profile_template import (
    standard_user_template)


class StandardUserGenerator:
    """Retrieve and modify standard user profiles"""
    def __init__(self):
        self.ix = -1

        # Read in user profiles
        self._load_user_profiles()

        # Generate valid profiles
        # This can be re-generated with an external call if profile overrides or attribute_dict overrides are required
        self.all_valid_profiles()

    def _load_user_profiles(self) -> None:
        """Load user profiles from file"""
        
        try:
            path = Path(__file__).parent / "data/user_profiles.json"
            with path.open() as f:
                self.user_profiles = json.load(f)
        except Exception:
            directory = "eval/library/conversation_generator/user_generation/data/"
            with open(os.path.join(directory, "user_profiles.json"), "r") as f:
                self.user_profiles = json.load(f)

    def all_valid_profiles(self, profile_overrides: dict = {},
                           attribute_dict_overrides: dict = {}) -> list[dict]:
        """Filter profiles and modify them according to any overrides, then return a list of profiles to use"""
        valid_profiles = []
        for p in self.user_profiles:
            profile_details = deepcopy(p)

            # Override values in the user profile_details if needed
            for override_key, override_value in profile_overrides.items():
                if override_key in profile_details:
                    profile_details[override_key] = override_value

            # Override values in the attribute dict if needed
            for override_key, override_value in attribute_dict_overrides.items():
                if override_key in profile_details['attribute_dict']:
                    profile_details['attribute_dict'][override_key] = override_value

            # Override null values with empty strings
            for key, value in profile_details.items():
                if value is None:
                    profile_details[key] = ""

            # Build prompt
            prompt = standard_user_template.replace(
                "{location}", profile_details['location']).replace(
                "{personality}", profile_details['personality']).replace(
                "{other}", profile_details['other'],
            )

            # Build profile in required format
            profile = {
                'prompt': prompt,
                'attributes': profile_details['attribute_dict'],
                'name': profile_details['name']
            }

            valid_profiles.append(profile)

        self.valid_profiles = valid_profiles
        return valid_profiles

    def generate_customer_profile(self) -> dict:
        """
        Keeps cycling through valid profiles and returns one at a time.
        The name is a bit misleading but it's to match the API in user_generation.random_user.RandomUserGenerator.
        """
        self.ix += 1
        if self.ix >= len(self.valid_profiles):
            self.ix = 0
        return self.valid_profiles[self.ix]
