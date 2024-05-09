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
        app_type: str,
    ):
        self.app_name = app_name
        self.app_type = app_type

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
    def from_dict(data: dict):
        """
        Creates a MappingColumn object from a dictionary.
        """
        return MappingColumn(data["source_name"], data["target_name"], data["data_type"])

class Mapping:
    """
    Represents a mapping file.

    Attributes:
        columns (List[MappingColumn]): A list of MappingColumn objects.
    """

    def __init__(self, name:str, columns: List[MappingColumn]):
        self.name = name
        self.columns = columns

    def to_dict(self):
        """
        Returns a dictionary of the mapping file.
        """
        return {
            "name": self.name,
            "columns": [column.to_dict() for column in self.columns]
        }

    @staticmethod
    def from_dict(data: dict):
        """
        Creates a Mapping object from a dictionary.
        """
        return Mapping(data["name"], [MappingColumn.from_dict(column) for column in data["columns"]])

class MappingList:
    """
    Represents a list of mapping files.

    Attributes:
        mappings (List[Mapping]): A list of Mapping objects.
    """

    def __init__(self, mappings: List[Mapping]):
        self.mappings = mappings

    def to_dict(self):
        """
        Returns a dictionary of the mapping list.
        """
        return {
            "mappings": [mapping.to_dict() for mapping in self.mappings]
        }

    @staticmethod
    def from_dict(data: dict):
        """
        Creates a MappingList object from a dictionary.
        """
        return MappingList([Mapping.from_dict(mapping) for mapping in data["mappings"]])

class DataSource:
    def __init__(self, type: str):
        self.type = type

class AzureMonitorDataSource(DataSource):
    """
    Represents a data source for Azure Monitor.
    
    Attributes:
        table (str): The table associated with the data source.
        workspace_id_secret_key (str): The secret key for the workspace ID.
    """
    
    def __init__(self, table: str, workspace_id_secret_key: str):
        super().__init__("azure_monitor")
        self.table = table
        self.workspace_id_secret_key = workspace_id_secret_key
    
    def to_dict(self):
        """
        Converts the AzureMonitorDataSource object to a dictionary.
        
        Returns:
            dict: A dictionary representation of the AzureMonitorDataSource object.
        """
        return {
            "type": self.type,
            "table": self.table,
            "workspace_id_secret_key": self.workspace_id_secret_key
        }
    
    @staticmethod
    def from_dict(data: dict):
        """
        Creates an AzureMonitorDataSource object from a dictionary.
        
        Args:
            data (dict): The dictionary containing the data source information.
        
        Returns:
            AzureMonitorDataSource: The created AzureMonitorDataSource object.
        """
        return AzureMonitorDataSource(data["table"], data["workspace_id_secret_key"])

class TransformationDTO:
    """
    Represents a transformation data transfer object.
    
    Attributes:
        name (str): The name of the transformation.
        mapping (Mapping): The mapping associated with the transformation.
        data (pd.DataFrame): The data associated with the transformation.
    """
    
    def __init__(self, name: str, mapping: Mapping, data: pd.DataFrame):
        self.name = name
        self.mapping = mapping
        self.data = data

class Transformer:
    """
    Represents a transformer object that performs data transformation.

    Args:
        name (str): The name of the transformer.
        chatbot_name (str): The name of the chatbot associated with the transformer.
        data_source (AzureMonitorDataSource): The data source for the transformer.
        mapping_list (MappingList): The list of mappings used for data transformation.
        endpoint (str): The endpoint where the transformed data will be sent.
        schedule (str): The schedule for running the transformer.
        schedule_start_time (str): The start time for the transformer schedule.

    Attributes:
        name (str): The name of the transformer.
        chatbot_name (str): The name of the chatbot associated with the transformer.
        data_source (AzureMonitorDataSource): The data source for the transformer.
        mapping_list (MappingList): The list of mappings used for data transformation.
        endpoint (str): The endpoint where the transformed data will be sent.
        schedule (str): The schedule for running the transformer.
        schedule_start_time (str): The start time for the transformer schedule.
    """

    def __init__(self, name: str, chatbot_name: str,
                 data_source: AzureMonitorDataSource, mapping_list: MappingList,
                 endpoint: str, schedule: str, schedule_start_time: str):
        self.name = name
        self.chatbot_name = chatbot_name
        self.data_source = data_source
        self.mapping_list = mapping_list
        self.endpoint = endpoint
        self.schedule = schedule
        self.schedule_start_time = schedule_start_time
    
    def get_mapping_list(self):
        """
        Returns the list of mappings used for data transformation.

        Returns:
            MappingList: The list of mappings used for data transformation.
        """
        return self.mapping_list

class DimMetrics:
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

class FactEvaluationMetric:
    def __init__(
        self,
        metric_id: int,
        evaluation_dataset_id: str,
        conversation_id: str,
        metadata_id: str,
        evaluator_metadata: str,
        metric_numeric_value: float,
        metric_str_value: str,
        metric_raw_value: str,
        fact_creation_time: datetime.datetime,
        created_by: str,
        updated_by: str
    ):
        self.metric_id = metric_id
        self.evaluation_dataset_id = evaluation_dataset_id
        self.conversation_id = conversation_id
        self.metadata_id = metadata_id
        self.evaluator_metadata = evaluator_metadata
        self.metric_numeric_value = metric_numeric_value
        self.metric_str_value = metric_str_value
        self.metric_raw_value = metric_raw_value
        self.fact_creation_time = fact_creation_time
        self.created_by = created_by
        self.updated_by = updated_by
