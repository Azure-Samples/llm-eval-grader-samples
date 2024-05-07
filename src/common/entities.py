import datetime
from typing import List, Union

import pandas as pd


class App:
    """
    Entity representing an application.

    Attributes:
        app_name (str): The name of the application. An application can be a bot, a component or a function.
        parent_app_name (str): The name of the parent application, if applicable. Example: Parent application of a component is a bot.
        app_type (str): The type of the application. Example: bot, component, function.
        parent_app_bot_name (str): The name of the parent bot application, if applicable.
        app_id (int): The ID of the application.
        parent_app_id (int): The ID of the parent application.
    """

    def __init__(
        self,
        app_name: str,
        parent_app_name: str,
        app_type: str,
        parent_app_bot_name: str = None,
        app_id: int = None,
        parent_app_id: int = None,
    ):
        self.app_name = app_name
        self.parent_app_name = parent_app_name
        self.app_type = app_type
        self.parent_app_bot_name = parent_app_bot_name
        self.app_id = app_id
        self.parent_app_id = parent_app_id


class Metric:
    """
    Represents a metric.

    Attributes:
        metric_name (str): The name of the metric.
        metric_type (str): The type of the metric (e.g., numerical, categorical).
        metric_allowed_values (list): A list of allowed values for the metric.
    """

    def __init__(self, metric_name: str, metric_type: str, metric_allowed_values: list, metric_id: int = None):
        self.metric_name = metric_name
        self.metric_type = metric_type
        self.metric_allowed_values = metric_allowed_values
        self.metric_id = metric_id

    def to_dict(self):
        """
        Returns a dictionary of metric name, type and allowed values.
        """
        return {
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "metric_allowed_values": self.metric_allowed_values
        }


class Evaluator:
    """
    Represents an evaluator.

    Attributes:
        evaluator_name (str): The name of the evaluator.
        evaluator_type (str): The type of the evaluation being run (e.g., LLM, human).
        evaluation_flow_path (str): The path to the evaluation promptflow.
        evaluation_endpoint (str): Name of the endpoint to which evaluation pipeline must be deployed.
        evaluation_schedule (str): The schedule for the evaluation pipeline to run in cron format.
        evaluation_schedule_start_time (str): The start time for the evaluation pipeline to run as per schedule.
        evaluation_metrics (list[Metric]): A list of Metric objects representing evaluation metrics.
        evaluation_metrics_version (float): The version of the evaluation metrics.
        app (App): An App object representing the associated application.
    """

    def __init__(
        self,
        evaluator_name: str,
        evaluator_type: str,
        evaluation_flow_path: str,
        evaluation_endpoint: str,
        evaluation_schedule: str,
        evaluation_schedule_start_time: str,
        evaluation_metrics: list[Metric],
        evaluation_metrics_version: float,
        app: App,
    ):
        self.evaluator_name = evaluator_name
        self.evaluator_type = evaluator_type
        self.evaluation_flow_path = evaluation_flow_path
        self.evaluation_endpoint = evaluation_endpoint
        self.evaluation_schedule = evaluation_schedule
        self.evaluation_schedule_start_time = evaluation_schedule_start_time
        self.evaluation_metrics = evaluation_metrics
        self.evaluation_metrics_version = evaluation_metrics_version
        self.app = app

class DimApplication:
    """
    Represents a DIM_APPLICATION entity.
    Args:
        app_id (int): The ID of the application.
        parent_app_id (int): The ID of the parent application.
        name (str): The name of the application.
        type (str): The type of the application, e.g., bot, component, function.

    """
    def __init__(
        self,
        app_id: int,
        parent_app_id: int,
        name: str,
        type: str,
    ):
        self.app_id = app_id
        self.parent_app_id = parent_app_id
        self.name = name
        self.type = type

class DimMetrics:
    """
    Represents a DIM_METRIC entity.
    Args:
        metric_name (str): The name of the metric.
        metric_version (float): The version of the metric.
        metric_type (str): The type of the metric (e.g., numerical, categorical).
        evaluator_name (str): The name of the evaluator.
        evaluator_type (str): The type of the evaluation being run (e.g., LLM, human).
        created_by (str): The user who is creating the metric dimension row.
        updated_date (datetime): The updated date.
        updated_by (str): The user who is updating the metric dimension row.

    """
    def __init__(
        self,
        metric_name: str,
        metric_version: float,
        metric_type: str,
        evaluator_name: str,
        evaluator_type: str,
        created_by: str,
        updated_date: datetime,
        updated_by: str
    ):
        self.metric_name = metric_name
        self.metric_version = metric_version
        self.metric_type = metric_type
        self.evaluator_name = evaluator_name
        self.evaluator_type = evaluator_type
        self.created_by = created_by
        self.updated_date = updated_date
        self.updated_by = updated_by

class FactInputDSMetric:
    """
    Represents a metric for a fact input dataset.

    Args:
        metric_id (int): The ID of the metric.
        evaluation_dataset_id (int): The ID of the evaluation dataset.
        app_id (int): The ID of the application.
        session_id (int): The ID of the session.
        router_function_id (int): The ID of the router function.
        metadata_id (int): The ID of the metadata.
        transcript_id (int): The ID of the transcript.
        evaluator_metadata (str): The evaluator metadata.
        metric_numeric_value (float): The numeric value of the metric.
        metric_str_value (str): The string value of the metric.
        metric_raw_value (str): The raw value of the metric.
        transcript_turn_seq_id (int): The ID of the transcript turn sequence.
        response_time (datetime): The response time.
        updated_date (datetime): The updated date.
        created_by (str): The creator of the metric.
        updated_by (str): The updater of the metric.
    """

    def __init__(
        self,
        metric_id: int,
        evaluation_dataset_id: int,
        app_id: int,
        session_id: int,
        router_function_id: int,
        metadata_id: int,
        transcript_id: int,
        evaluator_metadata: str,
        metric_numeric_value: float,
        metric_str_value: str,
        metric_raw_value: str,
        transcript_turn_seq_id: int,
        response_time: datetime,
        created_by: str,
        updated_date: datetime,
        updated_by: str,
    ):
        self.metric_id = metric_id
        self.evaluation_dataset_id = evaluation_dataset_id
        self.app_id = app_id
        self.session_id = session_id
        self.router_function_id = router_function_id
        self.metadata_id = metadata_id
        self.transcript_id = transcript_id
        self.evaluator_metadata = evaluator_metadata
        self.metric_numeric_value = metric_numeric_value
        self.metric_str_value = metric_str_value
        self.metric_raw_value = metric_raw_value
        self.transcript_turn_seq_id = transcript_turn_seq_id
        self.response_time = response_time
        self.created_by = created_by
        self.updated_date = updated_date
        self.updated_by = updated_by


class MappingColumn:
    """
    Represents a column in the mapping file.

    Attributes:
        source_name (str): The name of the source column.
        target_name (str): The name of the target column.
        data_type (str): The data type of the column.
    """

    def __init__(self, source_name: str, target_name: str, data_type: str):
        self.source_name = source_name
        self.target_name = target_name
        self.data_type = data_type

    def to_dict(self):
        """
        Returns a dictionary of source, target and data type of the column.
        """
        return {
            "source_name": self.source_name,
            "target_name": self.target_name,
            "data_type": self.data_type
        }

    @staticmethod
    def from_dict(column_dict: dict):
        """
        Returns a MappingColumn object from a dictionary of source, target and data type of the column.
        """
        return MappingColumn(
            column_dict["source_name"],
            column_dict["target_name"],
            column_dict["data_type"]
        )

class EvaluationType:
    """
    Represents an evaluation type with its evaluation and distribution.
    Attributes:
        evaluation (str): The evaluation type.
        distribution (float): The distribution value.
    """

    def __init__(self, evaluation: str, distribution: float):
        self.evaluation = evaluation
        self.distribution = distribution

class Transformer:
    """
    Represents a transformer which transforms the fact table data in Azure SQL in Silver Zone to fact and dimension tables in gold zone

    Attributes:
        name (str): The name of the transformation.
        bot_name (str): The name of the bot.
        app_types (list[str]): A list of application types.
        source_fact_table (str): The name of the source fact table.
        endpoint (str): The name of the endpoint to which transformation pipeline must be deployed.
        schedule (str): The schedule for the transformation pipeline to run in cron format.
        schedule_start_time (str): The start time for the transformation pipeline to run as per schedule.
        columns (list[MappingColumn]): A list of MappingColumn objects representing columns.
    """

    def __init__(
        self,
        name: str,
        bot_name: str,
        app_types: list[str],
        source_fact_table: str,
        source_fact_schema: str,
        endpoint: str,
        schedule: str,
        schedule_start_time: str,
        columns: list[MappingColumn] = None,
        evaluation_types: list[EvaluationType] = None,

    ):
        self.name = name
        self.bot_name = bot_name
        self.app_types = app_types
        self.source_fact_table = source_fact_table
        self.source_fact_schema = source_fact_schema
        self.endpoint = endpoint
        self.schedule = schedule
        self.schedule_start_time = schedule_start_time
        self.columns = columns
        self.evaluation_types = evaluation_types

    def get_columns(self) -> List[dict]:
        """
        Returns a list of dictionary of source, target and data type of the columns.

        Returns:
            List[dict]: A list of dictionary of source, target and data type of the columns.
        """
        columns = []
        for column in self.columns:
            columns.append(
                {
                    "source": column.source_name,
                    "target": column.target_name,
                    "data_type": column.data_type,
                }
            )
        return columns

    def get_evaluation_types(self) -> List[dict]:
        """
        Returns a list of dictionary of evaluation types and their distribution.

        Returns:
            List[dict]: A list of dictionary of evaluation types and their distribution.
        """
        evaluation_types = []
        for evaluation_type in self.evaluation_types:
            evaluation_types.append(
                {
                    "evaluation": evaluation_type.evaluation,
                    "distribution": evaluation_type.distribution,
                }
            )
        return evaluation_types

class BusinessMetric:
    """
    Represents a business metric.

    Attributes:
        metric_name (str): The name of the metric.
        metric_type (str): The type of the metric (e.g., numerical, categorical).
        metric_category (str): The category of the metric.
    """

    def __init__(self, metric_name: str, metric_type: str, metric_category: str):
        self.metric_name = metric_name
        self.metric_type = metric_type
        self.metric_category = metric_category


class BusinessMetricAggregator:
    """
    Represents a business metric aggregator.

    Attributes:
        bot_name (str): The name of the bot.
        source_table (str): The name of the source table.
        source_schema (str): The name of the source schema.
        business_metrics (List[BusinessMetric]): A list of BusinessMetric objects representing business metrics.
        columns (List[MappingColumn]): A list of MappingColumn objects representing columns.
    """

    def __init__(
        self,
        bot_name: str,
        source_table: str,
        source_schema: str,
        business_metrics: List[BusinessMetric],
        columns: List[MappingColumn],
    ):
        self.bot_name = bot_name
        self.source_table = source_table
        self.source_schema = source_schema
        self.business_metrics = business_metrics
        self.columns = columns

class FactOutputBusinessMetric:
    """
    Represents a business metric.

    Attributes:
        metric_name (str): The name of the metric.
        metric_type (str): The type of the metric (e.g., numerical, categorical).
        metric_category (str): The category of the metric.
        metric_source (str): The source of the metric.
        bot_name (str): The name of the bot.
        metric_positive_count (int): The positive count of the metric.
        metric_negative_count (int): The negative count of the metric.
        metric_raw_value (str): The raw value of the metric.
        metric_timestamp (datetime): The timestamp of the metric.
        business_unit (str): The business unit of the metric.
        router_function (str): The router function of the metric.
        aggregation_calc_date (datetime.datetime): The aggregation end date of the metric.
        created_by (str): The creator of the metric.
        updated_date (datetime.datetime): The date when the metric was last updated.
        updated_by (str): The user who last updated the metric.
    """

    def __init__(
        self,
        metric_name: str,
        metric_type: str,
        metric_category: str,
        metric_source: str,
        bot_name: str,
        metric_positive_count: int,
        metric_negative_count: int,
        metric_raw_value: str,
        metric_timestamp: datetime,
        business_unit: str,
        router_function: str,
        aggregation_calc_date: datetime,
        created_by: str,
        updated_date: datetime,
        updated_by: str,
    ):
        self.metric_name = metric_name
        self.metric_type = metric_type
        self.metric_category = metric_category
        self.metric_source = metric_source
        self.bot_name = bot_name
        self.metric_positive_count = metric_positive_count
        self.metric_negative_count = metric_negative_count
        self.metric_raw_value = metric_raw_value
        self.metric_timestamp = metric_timestamp
        self.business_unit = business_unit
        self.router_function = router_function
        self.aggregation_calc_date = aggregation_calc_date
        self.created_by = created_by
        self.updated_date = updated_date
        self.updated_by = updated_by

class MappingColumnNested:
    """
    Represents a nested column in the mapping file.

    Attributes:
        source_name (str): The name of the source column.
        target_name (str): The name of the target column.
        data_type (str): The data type of the column.
        sub_fields (List[MappingColumn]): A list of MappingColumn objects representing sub-fields.
    """
    def __init__(
        self,
        source_name: str,
        target_name: str,
        data_type: str,
        sort_by: str,
        sub_fields: List[MappingColumn],
    ):
        self.source_name = source_name
        self.target_name = target_name
        self.data_type = data_type
        self.sort_by = sort_by
        self.sub_fields = sub_fields

    def to_dict(self):
        """
        Returns a dictionary of source, target, data type, sort by and sub fields of the column.
        """
        return {
            "source_name": self.source_name,
            "target_name": self.target_name,
            "data_type": self.data_type,
            "sort_by": self.sort_by,
            "sub_fields": [field.to_dict() for field in self.sub_fields]
        }

    @staticmethod
    def from_dict(column_dict: dict):
        """
        Returns a MappingColumnNested object from a dictionary of source, target, data type, sort by and sub fields of the column.
        """
        return MappingColumnNested(
            column_dict["source_name"],
            column_dict["target_name"],
            column_dict["data_type"],
            column_dict["sort_by"],
            [MappingColumn.from_dict(field) for field in column_dict["sub_fields"]]
        )

class TaskMonk:
    """
    Represents a TaskMonk platform.

    Attributes:
        project_id (int): The ID of the project.
        batch_name_prefix (str): The prefix of the batch name.
    """
    def __init__(
        self,
        project_id: int,
        batch_name_prefix: str,
    ):
        self.project_id = project_id
        self.batch_name_prefix = batch_name_prefix

class HumanEvaluator:
    """
    Represents a human evaluator.

    Attributes:
        name (str): The name of the human evaluator.
        app_name (str): The name of the application.
        parent_app_name (str): The name of the parent application.
        platform_details (TaskMonk): A TaskMonk object representing the platform details.
        input_column_mapping (List[Union[MappingColumn, MappingColumnNested]]):
                A list of MappingColumn or MappingColumnNested objects representing input column mapping.
        output_column_mapping (List[Union[MappingColumn, MappingColumnNested]]):
                A list of MappingColumn or MappingColumnNested objects representing output column mapping.
    """
    def __init__(
        self,
        name: str,
        app_name: str,
        parent_app_name:str,
        platform_details: TaskMonk,
        input_column_mappings: List[Union[MappingColumn, MappingColumnNested]],
        output_column_mappings: List[Union[MappingColumn, MappingColumnNested]]
    ):
        self.name = name
        self.app_name = app_name
        self.parent_app_name = parent_app_name
        self.platform_details = platform_details
        self.input_column_mappings = input_column_mappings
        self.output_column_mappings = output_column_mappings

class HumanEvaluatorDetails:
    """
    Represents a human evaluator complete details along with metrics.

    Attributes:
        name (str): The name of the human evaluator.
        evaluators (List[Evaluator]): A list of Evaluator objects representing evaluators.
        human_evaluators (List[HumanEvaluator]): A list of HumanEvaluator objects representing human evaluators.
        upload_endpoint (str): The name of the upload endpoint.
        upload_schedule (str): The schedule for the upload endpoint to run in cron format.
        upload_schedule_start_time (str): The start time for the upload endpoint to run as per schedule.
        download_endpoint (str): The name of the download endpoint.
        download_schedule (str): The schedule for the download endpoint to run in cron format.
        download_schedule_start_time (str): The start time for the download endpoint to run as per schedule.
    """
    def __init__(
        self,
        name: str,
        evaluators: List[Evaluator],
        human_evaluators: List[HumanEvaluator],
        upload_endpoint: str,
        upload_schedule: str,
        upload_schedule_start_time: str,
        download_endpoint: str,
        download_schedule: str,
        download_schedule_start_time: str,
    ):
        self.name = name
        self.evaluators = evaluators
        self.human_evaluators = human_evaluators
        self.upload_endpoint = upload_endpoint
        self.upload_schedule = upload_schedule
        self.upload_schedule_start_time = upload_schedule_start_time
        self.download_endpoint = download_endpoint
        self.download_schedule = download_schedule
        self.download_schedule_start_time = download_schedule_start_time

class HumanEvalBatchStatus:
    """
    Represents a human evaluation batch status.

    Attributes:
        batch_id (str): The ID of the batch.
        batch_name (str): The name of the batch.
        project_id (str): The ID of the project.
        client (str): The name of the client.
        client_status (str): The status of the client.
        updated_date (datetime): The updated date.
        created_by (str): The user who is creating the batch status row.
        updated_by (str): The user who is updating the batch status row.
        evaluation_start_date (datetime): The start date of the batch evaluation.
        evaluation_end_date (datetime): The end date of the batch evaluation.
    """
    def __init__(
        self,
        batch_id: str,
        batch_name: str,
        project_id: str,
        client: str,
        client_status: str,
        updated_date: datetime,
        created_by: str,
        updated_by: str,
        evaluation_start_date: datetime,
        evaluation_end_date: datetime,
    ):
        self.batch_id = batch_id
        self.batch_name = batch_name
        self.project_id = project_id
        self.client = client
        self.client_status = client_status
        self.updated_date = updated_date
        self.created_by = created_by
        self.updated_by = updated_by
        self.evaluation_start_date = evaluation_start_date
        self.evaluation_end_date = evaluation_end_date


class HumanEvalMetrics:
    def __init__(
        self,
        metric: FactInputDSMetric,
        parent_metrics: Union[list[FactInputDSMetric], None],
        parent_metrics_unique_column: Union[str, None],
        metric_database_id: Union[int, None],
        parent_metric_database_ids: Union[list[int], None],
    ):
        self.metric = metric
        self.parent_metrics = parent_metrics
        self.parent_metrics_unique_column = parent_metrics_unique_column
        self.metric_database_id = metric_database_id
        self.parent_metric_database_ids = parent_metric_database_ids

class HumanEvalBatchDTO:
    def __init__(
        self,
        batch_id: str,
        project_id: str,
        downloaded_df: pd.DataFrame,
        eval_fact_df: pd.DataFrame,
        output_column_mappings: List[Union[MappingColumn, MappingColumnNested]],
        metrics_info: list[Metric],
        output_metrics: Union[list[HumanEvalMetrics], None]
    ):
        self.batch_id = batch_id
        self.project_id = project_id,
        self.downloaded_df = downloaded_df
        self.eval_fact_df = eval_fact_df
        self.output_column_mappings = output_column_mappings
        self.metrics_info = metrics_info
        self.output_metrics = output_metrics

class FactInputDSChildMetric:
    """
    Represents a metric for a fact child input dataset.

    Attributes:

    """
    def __init__(
        self,
        parent_metric_fact_id: int,
        metric_fact_id: int,
        updated_date: datetime,
        created_by: str,
        updated_by: str
    ):
        self.parent_metric_fact_id = parent_metric_fact_id
        self.metric_fact_id = metric_fact_id
        self.updated_date = updated_date
        self.created_by = created_by
        self.updated_by = updated_by
