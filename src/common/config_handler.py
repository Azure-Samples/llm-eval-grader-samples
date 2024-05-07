import yaml

from src.common.entities import (App, Evaluator, HumanEvaluator, HumanEvaluatorDetails,
                                 Metric, Transformer, MappingColumn, EvaluationType, MappingColumnNested, TaskMonk)
from src.common.logger import get_logger

logger = get_logger("config_handler")

def get_parent_app_bot_name(apps, app_name):
    """
    Returns the bot name of the parent app.

    Args:
        apps (str): List of apps and their information.
        app_name (str): Name of the app for which the parent bot name is to be found.

    Returns:
        str: Name of the parent bot.
    """
    for app in apps:
        if app['name'].lower() == app_name:
            if app["type"].lower() == "bot":
                return app_name
            else:
                return get_parent_app_bot_name(apps, app["parent_name"].lower())

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
        parent_app_name = app_info['parent_name'].lower()
        parent_app_bot_name=get_parent_app_bot_name(evaluation_config['apps'], parent_app_name).lower()
        app = App(
            app_name=app_name,
            parent_app_name=parent_app_name,
            parent_app_bot_name=parent_app_bot_name,
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

def get_human_evaluator_info(human_evaluators_config_file_path: str) -> list[HumanEvaluatorDetails]:
    """
    Reads the human evaluators configuration file and extracts information about human evaluators.

    Args:
        human_evaluators_config_file_path (str): Path to the human evaluators configuration file.

    Returns:
        list: A list of HumanEvaluatorDetails objects representing human evaluators.
    """
    logger.info("Reading human evaluators configuration file...")
    human_evaluators_config = load_yml_file_from_path(human_evaluators_config_file_path)

    human_evaluators_list = []

    for human_evaluator_info in human_evaluators_config['human_eval']:
        evaluators = human_evaluator_info.get('evaluators', [])
        if evaluators and any(evaluator.get('active') == "true" for evaluator in evaluators):
            active_evaluators = [evaluator for evaluator in evaluators if evaluator.get('active') == "true"]
            human_evaluators = []
            evaluators = []
            for active_evaluator in active_evaluators:
                app = App(
                    app_name=active_evaluator['app_name'].lower(),
                    parent_app_name=active_evaluator['parent_app_name'].lower(),
                    app_type=active_evaluator['app_type'].lower()
                )
                evaluator_info = next((evaluator for evaluator in human_evaluators_config['evaluators'] if evaluator['name'] == active_evaluator["name"]), None)
                evaluation_metrics = [
                    Metric(metric_name=metric['name'], metric_type=metric['value_type'], metric_allowed_values=metric['allowed_values'])
                    for metric in evaluator_info.get('metrics', [])
                ]
                evaluator = Evaluator(
                    evaluator_name=active_evaluator['name'],
                    evaluator_type=evaluator_info.get('type'),
                    evaluation_flow_path=None,
                    evaluation_endpoint=None,
                    evaluation_schedule=None,
                    evaluation_schedule_start_time=None,
                    evaluation_metrics=evaluation_metrics,
                    evaluation_metrics_version=evaluator_info.get('version'),
                    app=app,
                )
                evaluators.append(evaluator)
                platform_details = TaskMonk(
                    project_id=active_evaluator['evaluator_platform_details']['project_id'],
                    batch_name_prefix=active_evaluator['evaluator_platform_details']['batch_name_prefix']
                    ) if active_evaluator['evaluator_platform_details']['name'] == 'taskmonk' else None
                input_column_mappings = []
                for mapping in active_evaluator['input_column_mappings']:
                    if mapping.get('data_type') == 'nested':
                        sub_fields = []
                        for sub_field in mapping['sub_fields']:
                            sub_fields.append(MappingColumn(
                                source_name = sub_field["source"],
                                target_name = sub_field["target"],
                                data_type = sub_field["data_type"]
                            ))
                        input_column_mappings.append(MappingColumnNested(
                            source_name = None,
                            sort_by=mapping["sort_by"] if "sort_by" in mapping else None,
                            target_name = mapping["target"],
                            data_type = mapping["data_type"],
                            sub_fields = sub_fields
                        ))
                    else:
                        input_column_mappings.append(MappingColumn(
                            source_name = mapping["source"],
                            target_name = mapping["target"],
                            data_type = mapping["data_type"]
                        ))
                output_column_mappings = []
                for mapping in active_evaluator['output_column_mappings']:
                    if mapping.get('data_type') == 'nested':
                        sub_fields = []
                        for sub_field in mapping['sub_fields']:
                            sub_fields.append(MappingColumn(
                                source_name = sub_field["source"],
                                target_name = sub_field["target"],
                                data_type = sub_field["data_type"]
                            ))
                        output_column_mappings.append(MappingColumnNested(
                            source_name = mapping["source"],
                            target_name = None,
                            sort_by=mapping["sort_by"] if "sort_by" in mapping else None,
                            data_type = mapping["data_type"],
                            sub_fields = sub_fields
                        ))
                    else:
                        output_column_mappings.append(MappingColumn(
                            source_name = mapping["source"],
                            target_name = mapping["target"],
                            data_type = mapping["data_type"]
                        ))
                human_evaluator = HumanEvaluator(
                    name=active_evaluator['name'],
                    app_name=active_evaluator['app_name'],
                    parent_app_name=active_evaluator['parent_app_name'],
                    platform_details=platform_details,
                    input_column_mappings=input_column_mappings,
                    output_column_mappings=output_column_mappings,
                )
                human_evaluators.append(human_evaluator)
            human_evaluator_details = HumanEvaluatorDetails(
                name=human_evaluator_info['name'],
                evaluators=evaluators,
                human_evaluators=human_evaluators,
                upload_endpoint=[deployment['endpoint_name'] for deployment in human_evaluator_info.get('deployment_details', [])
                                 if deployment['name'] == 'upload'][0],
                upload_schedule=[deployment['schedule'] for deployment in human_evaluator_info.get('deployment_details', [])
                                 if deployment['name'] == 'upload'][0],
                upload_schedule_start_time=[deployment['schedule_start_time'] for deployment in human_evaluator_info.get('deployment_details', [])
                                             if deployment['name'] == 'upload'][0],
                download_endpoint=[deployment['endpoint_name'] for deployment in human_evaluator_info.get('deployment_details', [])
                                   if deployment['name'] == 'download'][0],
                download_schedule=[deployment['schedule'] for deployment in human_evaluator_info.get('deployment_details', [])
                                      if deployment['name'] == 'download'][0],
                download_schedule_start_time=[deployment['schedule_start_time'] for deployment in human_evaluator_info.get('deployment_details', [])
                                              if deployment['name'] == 'download'][0],
            )
            human_evaluators_list.append(human_evaluator_details)
    return human_evaluators_list

def get_app_info(evaluation_config_file_path: str) -> list[App]:
    """
    Reads the evaluation configuration file and extracts information about applications.

    Args:
        evaluation_config_file_path (str): Path to the evaluation configuration file.

    Returns:
        list: A list of App objects representing applications.
    """
    logger.info("Reading evaluation configuration file...")
    evaluation_config = load_yml_file_from_path(evaluation_config_file_path)

    apps_list = []

    for app_info in evaluation_config['apps']:
        app_name=app_info['name'].lower()
        parent_app_name = app_info['parent_name'].lower()
        parent_app_bot_name=get_parent_app_bot_name(evaluation_config['apps'], parent_app_name).lower()
        app = App(
            app_name=app_name,
            parent_app_name=parent_app_name,
            parent_app_bot_name=parent_app_bot_name,
            app_type=app_info['type']
        )
        apps_list.append(app)
    return apps_list

def get_transformer_info(transformation_config_file_path: str) -> list[Transformer]:
    """
    Reads the transformation configuration file and extracts information about transformers.

    Args:
        transformation_config_file_path (str): Path to the evaluation configuration file.

    Returns:
        list: A list of Transformer objects representing active transformers.
    """
    logger.info("Reading transformation configuration file...")
    with open(transformation_config_file_path, 'r') as file:
        try:
            transformation_config = yaml.safe_load(file)
        except yaml.YAMLError as ex:
            logger.exception(f"Error parsing the evaluation configuration file: {ex}")
            raise

    transformers_list = []

    for bot in transformation_config['transformation_config']:
        for transformer_info in bot.get('transformations', []):
            columns = []
            for mapping in transformer_info["mappings"]:
                columns.append(MappingColumn(
                    source_name = mapping["source"],
                    target_name = mapping["target"],
                    data_type = mapping["data_type"]
                ))
            evaluation_types = []
            for eval_type in transformer_info['evaluation_types']:
                evaluation_types.append(EvaluationType(
                    evaluation=eval_type['evaluation'],
                    distribution=eval_type['distribution']
                ))     
            transformers_list.append(Transformer(
                name=transformer_info['name'],
                bot_name = bot['bot_name'],
                app_types = transformer_info['app_types'],
                source_fact_schema=transformer_info['source_schema'],
                source_fact_table = transformer_info['source_table'],
                columns = columns,
                evaluation_types = evaluation_types,
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
