import datetime
from typing import List, Union
import pandas as pd


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
