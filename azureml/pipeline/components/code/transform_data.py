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

    @staticmethod
    def _get_logs(start_date: datetime, end_date: datetime, query: str) -> pd.DataFrame:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        load_dotenv()
        try:
            response = client.query_workspace(
                workspace_id=os.getenv("WORKSPACE_ID"),
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

    @staticmethod
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

    @staticmethod
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

    def transform(self):
        """
        Core logic of data transformation flow.
        """

        query_conversation_data = """ AppTraces | project TimeGenerated, Message, Properties | where Message == "conversation_data" """

        query_llm_data = """  AppTraces | project TimeGenerated, Message, Properties | where Message == "llm_data" """

        print("Data transformation started...")
        print("Reading data from different sources...")
        source_facts_conversation_df = self._get_logs(
            self.start_date, self.end_date, query_conversation_data
        )
        source_facts_llm_df = self._get_logs(self.start_date, self.end_date, query_llm_data)

        print(f"Read {len(source_facts_llm_df)} rows from azure monitor for llm data")
        print(f"Read {len(source_facts_conversation_df)} rows from azure monitor for llm data")

        print("Data transformation started for conversation level")
        df_conversation_mapped = self.transform_conversation_data(source_facts_conversation_df)
        print("Data transformation completed for conversation level")

        print("Data transformation started for llm level")
        df_llm_mapped = self.transform_llm_data(source_facts_llm_df)
        print("Data transformation completed llm level")


def parse_args():
    """
    Parses the user arguments.

    Returns:
        argparse.Namespace: The parsed user arguments.
    """
    parser = argparse.ArgumentParser(allow_abbrev=False, description="parse user arguments")
    parser.add_argument("--start_date", type=str, help="Start date", required=True)
    parser.add_argument("--end_date", type=str, help="End date", required=True)

    args, _ = parser.parse_known_args()
    return args


def main():
    args = parse_args()

    # Converting the start_date and end_date to datetime with timezone
    start_date = datetime.strptime(args.start_date, "%Y/%m/%d").replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(args.end_date, "%Y/%m/%d").replace(tzinfo=timezone.utc)

    transformation_processor = DataTransformer(
        start_date=start_date,
        end_date=end_date,
    )
    transformation_processor.transform()


if __name__ == "__main__":
    main()