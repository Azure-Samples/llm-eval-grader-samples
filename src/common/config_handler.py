import yaml

from src.common.entities import (App, Evaluator, HumanEvaluator, HumanEvaluatorDetails,
                                 Metric, Transformer, MappingColumn, EvaluationType, MappingColumnNested, TaskMonk)
from src.common.logger import get_logger

logger = get_logger("config_handler")

def load_yml_file_from_path(yml_file_path):
    """
    Load a YAML file from the given file path.

    Args:
        yml_file_path (str): The path to the YAML file.

    Returns:
        dict: The parsed YAML content.

    Raises:
        yaml.YAMLError: If there is an error parsing the YAML file.
    """
    with open(yml_file_path, 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as ex:
            logger.exception(f"Error parsing configuration file: {ex}")
            raise yaml.YAMLError(f"Error parsing configuration file: {ex}")
