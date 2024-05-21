
def load_json_file(path: str, name_data: str) -> list[dict]:
    """Load JSON file and modify its contents to include source data.

    Args:
        path (str): Path to the JSON file.
        name_data (str): Name of the source data.

    Returns:
        List[dict]: List of modified JSON data.
    """
    with open(path) as json_file:
        test_data_loaded = json.load(json_file)
        modified_test_data = []
        for json_data in test_data_loaded:
            json_data['source'] = name_data
            modified_test_data.append(json_data)

        return modified_test_data