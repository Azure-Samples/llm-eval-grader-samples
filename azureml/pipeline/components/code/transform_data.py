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