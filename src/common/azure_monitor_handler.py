import argparse
import ast
import datetime
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import pandas as pd
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus

class AzureMonitorHandler:
    
    def _get_logs(start_date: datetime, end_date: datetime, query: str) -> pd.DataFrame:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        load_dotenv()
        try:
            response = client.query_workspace(
                workspace_id="24bbb4b3-a8e3-4a98-9c0d-2a48494c5e35",
                query=query,
                timespan=(start_date, end_date),
            )
            if response.status == LogsQueryStatus.PARTIAL:
                error = response.partial_error
                data = response.partial_data
                print(error)
            elif response.status == LogsQueryStatus.SUCCESS:
                data = response.tables
            for table in data:
                df_logs = pd.DataFrame(data=table.rows, columns=table.columns)
                print(df_logs)
        except HttpResponseError as err:
            print("something fatal happened")
            print(err)
        return df_logs