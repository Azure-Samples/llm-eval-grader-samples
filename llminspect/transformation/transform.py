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


class DataTransformer:
    """
    Class representing data transformer for transferring data from silver to gold zone.
    """

    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date


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


    def transform_conversation_data(source_facts_conversation_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the conversation data.
        """
        df_conversation_mapped = pd.DataFrame(
            columns=["conversation_id", "turn_id", "query", "response", "timestamp"]
        )
        for i in range(source_facts_conversation_df.shape[0]):
            df_conversation_mapped.loc[i] = [
                ast.literal_eval(source_facts_conversation_df["Properties"].iloc[i])[
                    "conversation_id"
                ],
                ast.literal_eval(source_facts_conversation_df["Properties"].iloc[i])["turn_id"],
                ast.literal_eval(source_facts_conversation_df["Properties"].iloc[i])["query"],
                ast.literal_eval(source_facts_conversation_df["Properties"].iloc[i])["response"],
                source_facts_conversation_df["TimeGenerated"].iloc[i],
            ]
        return df_conversation_mapped


    def transform_llm_data(source_facts_llm_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the llm data.
        """
        df_llm_mapped = pd.DataFrame(
            columns=[
                "context",
                "response",
                "conversation_id",
                "turn_id",
                "query",
                "intent",
                "model",
                "timestamp",
        ])
        for i in range(source_facts_llm_df.shape[0]):
            if "llm_response" not in ast.literal_eval(source_facts_llm_df["Properties"].iloc[i]):
                continue
            if "context" in ast.literal_eval(source_facts_llm_df["Properties"].iloc[i]):
                df_llm_mapped.loc[i] = [
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["context"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["llm_response"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["conversation_id"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["turn_id"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["query"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["intent"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["model"],
                    source_facts_llm_df["TimeGenerated"].iloc[i],
                ]
            else:
                df_llm_mapped.loc[i] = [
                    "",
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["llm_response"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["conversation_id"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["turn_id"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["query"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["intent"],
                    ast.literal_eval(source_facts_llm_df["Properties"].iloc[i])["model"],
                    source_facts_llm_df["TimeGenerated"].iloc[i],
                ]
        df_llm_mapped["response"] = df_llm_mapped["response"].apply(
            lambda x: json.loads(x)["choices"][0]["message"]["content"] if x != "" else x
        )
        return df_llm_mapped

    