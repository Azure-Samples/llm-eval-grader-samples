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
from src.transformation.transform  import DataTransformer






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
    parser = argparse.ArgumentParser(
        allow_abbrev=False, description="parse user arguments"
    )
    parser.add_argument("--bot_name", type=str, help="Bot name", required=True)
    parser.add_argument("--app_types", type=str, help="Apps type", required=True)
    parser.add_argument("--fact_table_name", type=str, help="Fact table name", required=True)
    parser.add_argument("--fact_schema_name", type=str, help="Fact schema name", required=True)
    parser.add_argument("--columns", type=str, help="Columns", required=True)
    parser.add_argument("--evaluation_types", type=str, help="Evaluation types", required=True)
    parser.add_argument("--start_date", type=str, help="Start date", required=True)
    parser.add_argument("--end_date", type=str, help="End date", required=True)
    parser.add_argument("--key_vault_url", type=str, help="Key vault url", required=True)
    parser.add_argument("--fact_evaluation_output", type=str, help="Fact evaluation output path", required=True)
    parser.add_argument("--dim_metadata_output", type=str, help="Dim metadata output path", required=True)
    parser.add_argument("--dim_conversation_output", type=str, help="Dim sessions output path", required=True)
    args, _ = parser.parse_known_args()
    return args

def main():
    args = parse_args()
    columns = ast.literal_eval(args.columns)    
    evaluation_types = ast.literal_eval(args.evaluation_types)
    app_types = ast.literal_eval(args.app_types)
   
    # Converting the start_date and end_date to datetime with timezone
    start_date = datetime.strptime(args.start_date, "%Y/%m/%d").replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(args.end_date, "%Y/%m/%d").replace(tzinfo=timezone.utc)
    
    transformation_processor = DataTransformer(key_vault_url=args.key_vault_url, start_date=start_date,
                                            end_date=end_date, columns=columns, evaluation_types=evaluation_types, app_types=app_types, bot_name=args.bot_name,
                                            source_fact_schema_name=args.fact_schema_name,
                                            source_fact_table_name=args.fact_table_name,
                                            dim_metadata_output_path=args.dim_metadata_output,
                                            dim_conversation_output_path=args.dim_conversation_output,
                                            fact_evaluation_output_path=args.fact_evaluation_output)
    transformation_processor.transform()


if __name__ == "__main__":
    main()