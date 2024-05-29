import json
import os
import argparse
import datetime
from copy import deepcopy
# from src.main.ca.canadiantire.pos.models.constants import CONTEXT_VISITED_COMPONENTS


log_directories = [
    'logs/',
]

default_component_name = 'LocationExtractor'
default_component_type = 'LocationAgent'
default_test_cases_to_extract = {
    "4d20609952f74240840310cf4650f7c3": 5
}

component_name = ''
component_type = ''

output_base_dir_template = 'logs/extracted_test_cases/{component_type}/{component_name}/test-data/'

_MATCH_ALL_WILDCARD = '*'


def extract_test_cases(test_cases_to_extract: dict, split_into_visited_components: bool):
    test_cases = []

    # Create output file for this current run
    output_filename = f'new_test_cases_{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.json'

    for directory in log_directories:
        for filename in os.listdir(directory):
            if not filename.endswith('.xlsx'):
                if os.path.isfile(os.path.join(directory, filename)):
                    test_cases += find_test_cases(f'{directory}/{filename}', test_cases_to_extract,
                                                  split_into_visited_components)

    consolidated_test_cases = consolidate_test_cases_by_component(test_cases)

    for component in consolidated_test_cases:
        output_base_dir = output_base_dir_template.format(component_name=component, component_type=component_type)

        if not os.path.exists(output_base_dir):
            os.makedirs(output_base_dir)

        destination_filename = os.path.join(output_base_dir, output_filename)

        # Print extracted cases
        with open(destination_filename, 'a') as f:
            json.dump(consolidated_test_cases[component], f, indent=4)


def consolidate_test_cases_by_component(test_cases: list[dict[str, object]]) -> dict[str, list[object]]:
    """Consolidate lists of component + test cases into dictionary of unique components
    w/ lists of test cases:
    [ {'component_a': {test case1}}, {'component_b': {test case2}}, {'component_a': {test case3}}] ->
    {'component_a': [{test case 1}, {test case3}], 'component_b': [{test case2}]}

    Args:
        test_cases (list[dict[str:object]]): List of dictionaries containing the component names + test cases

    Returns:
        dict[str, list[object]]: The same test cases in a dictionary with the component name as the key
        and a list of the test cases as the value
    """
    output_cases_by_component = {}
    for test_case in test_cases:
        for _, (k, v) in enumerate(test_case.items()):
            if k not in output_cases_by_component:
                output_cases_by_component[k] = [v]
            else:
                output_cases_by_component[k].append(v)

    return output_cases_by_component


def find_test_cases(filename: str, test_cases_to_extract: dict, split_into_visited_components: bool) -> list[dict]:
    test_cases = []

    with open(filename, 'r') as file:
        file_contents = file.read()
        json_objects = file_contents.split('~~~NEW_CONVERSATION~~~')

        for obj in json_objects:
            try:
                conversation = json.loads(obj)
                if isinstance(conversation, dict):
                    if is_test_case_conversation(test_cases_to_extract, conversation):
                        test_cases += create_test_cases(conversation, test_cases_to_extract,
                                                        split_into_visited_components)
            except json.JSONDecodeError:
                pass

    return test_cases


def create_test_cases(conversation: dict, test_cases_to_extract: dict, split_into_visited_components: bool) \
        -> list[dict]:
    test_cases = []

    conversation_id = conversation['conversation_id']

    # Take a deep copy of this. If it contains wildcards, we will
    # expand the wildcards into the actual conversation_ids + messageIds
    test_cases_to_extract_copy = deepcopy(test_cases_to_extract)

    # Handle integers and lists/tuples for message_id input
    if _MATCH_ALL_WILDCARD in test_cases_to_extract_copy:
        test_cases_to_extract_copy[conversation_id] = test_cases_to_extract_copy[_MATCH_ALL_WILDCARD]

    if test_cases_to_extract_copy[conversation_id] == _MATCH_ALL_WILDCARD:
        test_cases_to_extract_copy[conversation_id] = [msg['messageId'] for msg in conversation['conversation_history']]

    if hasattr(test_cases_to_extract_copy[conversation_id], '__iter__'):
        message_ids = test_cases_to_extract_copy[conversation_id]
    else:
        message_ids = [test_cases_to_extract_copy[conversation_id]]

    for message_id in message_ids:
        # Logic to build test case in correct format
        for msg in conversation['conversation_history']:
            if message_id == msg['messageId']:
                test_case = {
                    "test_case_id": f'{str(conversation_id)}-{str(message_id)}',
                    "expected_output": msg['content'],
                    "customer_profile": conversation['customer_profile']
                }

                if "context" in msg:
                    test_case["context"] = deepcopy(msg["context"])

                # if split_into_visited_components:
                #     if "context" in msg and CONTEXT_VISITED_COMPONENTS in msg["context"]:
                #         for visited_component in msg["context"][CONTEXT_VISITED_COMPONENTS]:
                #             test_cases.append({visited_component: test_case})
                # else:
                test_cases.append({component_name: test_case})
                break

    return test_cases


def is_test_case_conversation(test_cases_to_extract: dict, conversation: dict):
    if (_MATCH_ALL_WILDCARD in test_cases_to_extract):
        return True
    else:
        return 'conversation_id' in conversation and conversation['conversation_id'] in test_cases_to_extract


def validate_test_cases_to_extract(test_cases_to_extract: dict):
    for key in test_cases_to_extract.keys():
        if type(key) is not str:
            raise ValueError(f'All test case keys must be strings (wildcard {_MATCH_ALL_WILDCARD} is also OK). '
                             'Offending key: {key}')

    value_error_message = 'Message ids must be specified as integers, a list of integers, or ' \
                          f'the wildcard ({_MATCH_ALL_WILDCARD}) character).'

    for value in test_cases_to_extract.values():
        if type(value) is str and value == _MATCH_ALL_WILDCARD:
            continue

        if type(value) is int:
            continue

        if type(value) is list:
            for value_part in value:
                if type(value_part) is not int:
                    raise ValueError(f'{value_error_message} Offending value: {value}')

            continue

        raise ValueError(f'{value_error_message} Offending value: {value}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--component_name", type=str, required=False, default=default_component_name)
    parser.add_argument("--component_type", type=str, required=False, default=default_component_type)
    parser.add_argument("--test_cases_to_extract", type=str, required=False, default=str(default_test_cases_to_extract))
    parser.add_argument("--split_into_visited_components", type=bool, required=False, default=False)
    args, _ = parser.parse_known_args()
    component_name = args.component_name
    component_type = args.component_type
    test_cases_to_extract = json.loads(args.test_cases_to_extract)
    validate_test_cases_to_extract(test_cases_to_extract)
    extract_test_cases(test_cases_to_extract, args.split_into_visited_components)
