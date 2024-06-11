import yaml

from llmevalgrader.common.entities import (App, Evaluator, Metric, Transformer, MappingColumn, AzureMonitorDataSource,MappingList)
from llmevalgrader.common.logger import get_logger

logger = get_logger("config_handler")


def get_transformer_info(transformation_config_file_path: str) -> list[Transformer]:
    """   
    Load the transformation configuration from the given file path.

    Args:
        transformation_config_file_path (str): The file path of the transformation configuration file.

    Returns:
        list[Transformer]: A list of Transformer objects representing the loaded configuration.

    Raises:
        yaml.YAMLError: If there is an error parsing the transformation configuration file.
    """
    logger.info("Reading transformation configuration file...")
    with open(transformation_config_file_path, 'r') as file:
        try:
            transformation_config = yaml.safe_load(file)
        except yaml.YAMLError as ex:
            logger.exception(f"Error parsing the evaluation configuration file: {ex}")
            raise

    transformers_list = []

    for transformer_info in transformation_config.get('transformation_config', []):
        transformers_list.append(Transformer(
            name=transformer_info["name"],
            chatbot_name=transformer_info['chatbot_name'],
            data_source=AzureMonitorDataSource.from_dict(transformer_info["source"]),
            mapping_list=MappingList.from_dict(transformer_info),
            endpoint=transformer_info['endpoint_name'],
            schedule=transformer_info['schedule'],
            schedule_start_time=transformer_info['schedule_start_time'],
        ))
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

def get_evaluator_info(evaluation_config_file_path):
    """
    Reads the evaluation configuration file and extracts information about active evaluators.

    Args:
        evaluation_config_file_path (str): Path to the evaluation configuration file.

    Returns:
        list: A list of Evaluator objects representing active evaluators.
    """
    logger.info("Reading evaluation configuration file...")
    evaluation_config = load_yml_file_from_path(evaluation_config_file_path)

    evaluators_list = []

    for app_info in evaluation_config['apps']:
        app_name=app_info['name'].lower()
        app = App(
            app_name=app_name,
            app_type=app_info['type']
        )
        evaluators = app_info.get('evaluators', [])
        if evaluators and any(evaluator.get('active') == "true" for evaluator in evaluators):
            active_evaluators = [evaluator for evaluator in evaluators if evaluator.get('active') == "true"]
            for active_evaluator in active_evaluators:
                evaluator_info = next((evaluator for evaluator in evaluation_config['evaluators'] if evaluator['name'] == active_evaluator["name"]), None)
                evaluation_metrics = [
                    Metric(metric_name=metric['name'], metric_type=metric['value_type'], metric_allowed_values=metric['allowed_values'])
                    for metric in evaluator_info.get('metrics', [])
                ]
                evaluator = Evaluator(
                    evaluator_name=active_evaluator['name'],
                    evaluator_type=evaluator_info.get('type'),
                    evaluation_flow_path=evaluator_info.get('flow_path'),
                    evaluation_endpoint=active_evaluator['endpoint_name'],
                    evaluation_schedule=active_evaluator['schedule'],
                    evaluation_schedule_start_time=active_evaluator['schedule_start_time'],
                    evaluation_metrics=evaluation_metrics,
                    evaluation_metrics_version=evaluator_info.get('version'),
                    app=app,
                )
                evaluators_list.append(evaluator)
    return evaluators_list