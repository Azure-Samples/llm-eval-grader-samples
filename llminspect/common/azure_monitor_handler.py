import datetime
from logging import Logger
from datetime import datetime
import pandas as pd
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus

from llminspect.common.logger import get_logger

class AzureMonitorHandler:
    def __init__(self, workspace_id: str, logger: Logger = get_logger("azure_monitor_handler")):
        self.workspace_id = workspace_id
        self.logger = logger

    def get_logs_by_time_range(self, start_date: datetime, end_date: datetime, query: str) -> pd.DataFrame:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        try:
            self.logger.info(f"Querying logs from {start_date} to {end_date}")
            self.logger.info(f"Query: {query}")
            response = client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=(start_date, end_date),
            )
            if response.status == LogsQueryStatus.PARTIAL:
                error = response.partial_error
                data = response.partial_data
                self.logger.error(error)
            elif response.status == LogsQueryStatus.SUCCESS:
                data = response.tables
            for table in data:
                df_logs = pd.DataFrame(data=table.rows, columns=table.columns)
                self.logger.info(f"Gathered logs: {df_logs.shape[0]} rows")
        except HttpResponseError as err:
            self.logger.error("Something fatal happened")
            self.logger.error(err)
        return df_logs
