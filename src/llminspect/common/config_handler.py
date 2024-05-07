import yaml

from src.common.entities import (Transformer, MappingColumn, EvaluationType, AzureMonitorDataSource,MappingList)
from src.common.logger import get_logger

logger = get_logger("config_handler")


def get_transformer_info(transformation_config_file_path: str) -> list[Transformer]:
    """   
    Load the transformation configuration from the given file path.
    """
    logger.info("Reading transformation configuration file...")
    with open(transformation_config_file_path, 'r') as file:
        try:
            transformation_config = yaml.safe_load(file)
        except yaml.YAMLError as ex:
            logger.exception(f"Error parsing the evaluation configuration file: {ex}")
            raise

    transformers_list = []

 
    for transformer_info in transformation_config.get('transformations', []):
        columns = []
        for mapping in transformer_info["mappings"]:
            columns.append(MappingColumn(
                source_name = mapping["source"],
                target_name = mapping["target"],
                data_type = mapping["data_type"]
            ))
          
        transformers_list.append(Transformer(
            name=transformation_config["transformation_config"][0]["transformations"][0]["name"]),
            chatbot_name = transformation_config["transformation_config"][0]['chatbot_name'],
            data_source =AzureMonitorDataSource.from_dict(transformation_config["transformation_config"][0]["transformations"][0]["source"]),
            columns = MappingList.from_dict(transformation_config["transformation_config"][0]["transformations"][0]),
            endpoint=transformer_info['endpoint_name'],
            schedule=transformer_info['schedule'],
            schedule_start_time=transformer_info['schedule_start_time'],
        )
    return transformers_list


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
