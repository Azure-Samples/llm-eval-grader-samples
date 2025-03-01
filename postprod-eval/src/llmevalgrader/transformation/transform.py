# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import ast
import datetime
import json
from logging import Logger
from datetime import datetime
import numpy as np
import pandas as pd

from llmevalgrader.common.logger import get_logger
from llmevalgrader.common.azure_monitor_handler import AzureMonitorHandler
from llmevalgrader.common.get_secret import get_key_vault_secret
from llmevalgrader.common.entities import AzureMonitorDataSource, MappingList, TransformationDTO


class DataTransformer:
    """
    Class representing data transformer for transferring data from silver to gold zone.
    """

    def __init__(
            self,
            start_date: datetime,
            end_date: datetime,
            key_vault_url: str,
            data_source: AzureMonitorDataSource,
            mappings: MappingList,
            logger: Logger = get_logger("data_transformer")):
        self.start_date = start_date
        self.end_date = end_date
        self.key_vault_url = key_vault_url
        self.data_source = data_source
        self.mappings = mappings
        self.logger = logger

        self.azure_monitor_handler = AzureMonitorHandler(
            workspace_id=get_key_vault_secret(key_vault_url, self.data_source.workspace_id_secret_key))
        
    def _transform_conversation_data(self, transformation_dto: TransformationDTO) -> TransformationDTO:
        """
        Transforms the conversation data.

        Args:
            transformation_dto (TransformationDTO): The transformation data transfer object.

        Returns:
            TransformationDTO: The transformed transformation data transfer object.
        """
        df_conversation_mapped = pd.DataFrame(
            columns=[column.target_name for column in transformation_dto.mapping.columns]
        )
        for column in transformation_dto.mapping.columns:
            df_conversation_mapped[column.target_name] = transformation_dto.data["Properties"].apply(
                lambda x: ast.literal_eval(x)[column.source_name] if column.source_name in ast.literal_eval(x) else None
            )
            if column.source_name == "TimeGenerated":
                df_conversation_mapped[column.target_name] = pd.to_datetime(
                    transformation_dto.data[column.source_name], unit="ms"
                )
        df_conversation_mapped["app_type"] = "conversation"
        transformation_dto.data = df_conversation_mapped
        return transformation_dto


    def _transform_llm_data(self, transformation_dto: TransformationDTO) -> TransformationDTO:
            """
            Transforms the llm data.

            Args:
                transformation_dto (TransformationDTO): The transformation DTO containing the data and mapping information.

            Returns:
                TransformationDTO: The transformed transformation DTO.

            """
            df_llm_mapped = pd.DataFrame(
                columns=[column.target_name for column in transformation_dto.mapping.columns]
            )
            for column in transformation_dto.mapping.columns:
                df_llm_mapped[column.target_name] = transformation_dto.data["Properties"].apply(
                    lambda x: ast.literal_eval(x)[column.source_name] if column.source_name in ast.literal_eval(x) else None
                )
                if column.source_name == "TimeGenerated":
                    df_llm_mapped[column.target_name] = pd.to_datetime(
                        transformation_dto.data[column.source_name], unit="ms"
                    )
            df_llm_mapped["app_type"] = "llm"
            df_llm_mapped["response"] = transformation_dto.data["Properties"].apply(
                lambda x: json.loads(json.loads(x)["llm_response"])["choices"][0]["message"]["content"] if x != np.nan and "llm_response" in json.loads(x) else None
            )
            transformation_dto.data = df_llm_mapped
            return transformation_dto

    def get_logs(self) -> list[TransformationDTO]:
            """
            Gets the logs from Azure Monitor.

            Returns:
                A list of TransformationDTO objects representing the logs retrieved from Azure Monitor.
            """
            transformation_dtos = []
            for mapping in self.mappings.mappings:
                query = f"AppTraces | project TimeGenerated, Message, Properties | where Message == '{mapping.name}'"
                df_logs = self.azure_monitor_handler.get_logs_by_time_range(
                    self.start_date, self.end_date, query
                )
                transformation_dtos.append(TransformationDTO(name=mapping.name, mapping=mapping, data=df_logs))
                self.logger.info(f"Shape of the data after getting logs: {df_logs.shape} for {mapping.name}")
            return transformation_dtos
    
    def transform_data(self, transformation_dtos: list[TransformationDTO]) -> list[TransformationDTO]:
        """
        Transforms the data.

        Args:
            transformation_dtos (list[TransformationDTO]): A list of TransformationDTO objects representing the data to be transformed.

        Returns:
            list[TransformationDTO]: A list of TransformationDTO objects representing the transformed data.
        """
        post_transformation_dtos = []
        for transformation_dto in transformation_dtos:
            if transformation_dto.mapping.name == "conversation_data":
                self.logger.info(f"Data transformation started for conversation level for {transformation_dto.name}")
                self.logger.info(f"Shape of the data before transformation: {transformation_dto.data.shape}")
                transformation_dto = self._transform_conversation_data(transformation_dto)
                self.logger.info(f"Shape of the data after transformation: {transformation_dto.data.shape}")
            elif transformation_dto.mapping.name == "llm_data":
                self.logger.info(f"Data transformation started for llm level: {transformation_dto.name}")
                self.logger.info(f"Shape of the data before transformation: {transformation_dto.data.shape}")
                transformation_dto = self._transform_llm_data(transformation_dto)
                self.logger.info(f"Shape of the data after transformation: {transformation_dto.data.shape}")
            post_transformation_dtos.append(transformation_dto)
        self.logger.info("Data transformation completed.")
        return post_transformation_dtos
    
    def clean_data(self, transformation_dtos: list[TransformationDTO]) -> list[TransformationDTO]:
        """
        Cleans the data by removing rows with missing values.

        Args:
            transformation_dtos (list[TransformationDTO]): A list of TransformationDTO objects representing the data to be cleaned.

        Returns:
            list[TransformationDTO]: The cleaned list of TransformationDTO objects.
        """
        for transformation_dto in transformation_dtos:
            self.logger.info(f"Data cleaning started for: {transformation_dto.name}")
            self.logger.info(f"Shape of the data before cleaning: {transformation_dto.data.shape}")
            transformation_dto.data = transformation_dto.data.dropna()
            self.logger.info(f"Shape of the data after cleaning: {transformation_dto.data.shape}")
        self.logger.info("Data cleaning completed.")
        return transformation_dtos
    
    def add_optional_extra_columns(self, transformation_dtos: list[TransformationDTO],
                                   extra_column: str, extra_value: str) -> list[TransformationDTO]:
        """
        Adds optional extra columns.

        Args:
            transformation_dtos (list[TransformationDTO]): A list of TransformationDTO objects.
            extra_column (str): The name of the extra column to add.
            extra_value (str): The value to assign to the extra column.

        Returns:
            list[TransformationDTO]: The updated list of TransformationDTO objects with the extra column added.
        """
        self.logger.info(f"Adding optional extra column: {extra_column} with value: {extra_value}")
        for transformation_dto in transformation_dtos:
            transformation_dto.data[extra_column] = extra_value
        return transformation_dtos
    
    def concat_data(self, transformation_dtos: list[TransformationDTO]) -> pd.DataFrame:
        """
        Concatenates the data.

        Args:
            transformation_dtos (list[TransformationDTO]): A list of TransformationDTO objects containing the data to be concatenated.

        Returns:
            pd.DataFrame: The concatenated data as a pandas DataFrame.
        """
        self.logger.info("Concatenating the data.")
        concat_df = pd.concat([transformation_dto.data for transformation_dto in transformation_dtos])
        self.logger.info(f"Shape of the concatenated data: {concat_df.shape}")
        self.logger.info(f"Columns of the concatenated data: {concat_df.columns.to_list()}")
        return concat_df
    
    def fill_missing_values(self, concat_data: pd.DataFrame) -> pd.DataFrame:
        """
        Fills the missing values in the given DataFrame.

        Args:
            concat_data (pd.DataFrame): The DataFrame containing the data to be filled.

        Returns:
            pd.DataFrame: The DataFrame with missing values filled.

        """
        self.logger.info("Filling missing values.")
        concat_data = concat_data.fillna("NA")
        self.logger.info(f"Shape of the data after filling missing values: {concat_data.shape}")
        return concat_data
