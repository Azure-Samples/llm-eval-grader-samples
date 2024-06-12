""""Calculate grade"""

from typing import Any, Union


def exact_match_score(expected_output: Any, result: Any) -> int:
    if not result and not expected_output:
        return 1
    elif result == expected_output:
        return 1
    else:
        return 0


def is_value_in_list(expected_output: Union[list[str], str, None], result: Union[str, None]) -> int:
    if expected_output is None and result is None:
        return 1
    
    if isinstance(expected_output, str) and isinstance(result, str):
        if expected_output.strip() == result.strip():
            return 1
    
    if isinstance(expected_output, list) and isinstance(result, str):
        if any(item.strip() == result.strip() for item in expected_output):
            return 1

    return 0


def assess_preference_match(expected_output: dict, actual_output: dict) -> float:
    """
    Calculate the score for a single test case based on expected and actual outputs.
    Handles both boolean and list values.
   
    :param expected_output: A dictionary of expected preferences with boolean or list values.
    :param actual_output: A dictionary of actual preferences identified with boolean or list values.
    :return: The normalized score for the test case.
    """
    if not expected_output:
        if not actual_output:
            return 1
        return 0

    correct_identifications = 0
    false_positives = 0
   
    # Check for correct identifications and false positives
    for key, value in actual_output.items():
        if key in expected_output:
            expected_value = expected_output[key]
            # Handling both boolean and list values
            if isinstance(value, list) and isinstance(expected_value, list):
                if sorted(value) == sorted(expected_value):
                    correct_identifications += 1
                else:
                    false_positives += 1
            elif value == expected_value:
                correct_identifications += 1
            else:
                false_positives += 1
        else:
            false_positives += 1
   
    # Calculate raw score
    raw_score = correct_identifications - false_positives
   
    # Calculate maximum possible score
    max_score = len(expected_output)
   
    # Normalize score
    normalized_score = raw_score / max_score if max_score > 0 else 0
   
    # Ensure minimum score is 0
    normalized_score = round(max(0, normalized_score), 2)
   
    return normalized_score
