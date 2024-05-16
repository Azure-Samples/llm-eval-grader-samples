"""Calcualte grade"""

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