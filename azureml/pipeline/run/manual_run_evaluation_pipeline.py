import argparse
import os
from datetime import datetime

from azure.ai.ml import Input, MLClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pathlib import Path


def valid_date(datestring):
    """Validate the date format

    Args:
        datestring (str): The date string

    Raises:
        argparse.ArgumentTypeError: Not a valid date

    Returns:
        datetime: The datetime object
    """
    try:
        input_datetime = datetime.strptime(datestring, "%Y/%m/%d %H:%M")
        if input_datetime > datetime.now():
            raise ValueError(
                "Date should be in the past, Input given is: '{0}'.".format(datestring)
            )

        return datestring
    except ValueError as err:
        raise argparse.ArgumentTypeError(err.args[0])


def parse_args():
    """Parse command line arguments

    Returns:
        Namespace: The parsed arguments
    """

    parser = argparse.ArgumentParser(description="Process command line arguments")
    parser.add_argument(
        "--evaluation_start_date",
        help="Date to run the aggregation for in format YYYY/MM/DD HH:MM",
        required=True,
        type=valid_date,
    )
    parser.add_argument(
        "--evaluation_end_date",
        help="Date to run the aggregation for in format YYYY/MM/DD HH:MM",
        required=True,
        type=valid_date,
    )
    parser.add_argument(
        "--endpoint_name",
        help="Endpoint name to run the aggregation for",
        required=False,
    )
    parser.add_argument("--retry_pipeline", help="Retry Pipeline flag", required=False)
    return parser.parse_args()


def get_ml_client():
    """Get the ML client

    Returns:
        MLClient: The ML client
    """
    dotenv_path = Path("../deploy/.env")
    load_dotenv(dotenv_path=dotenv_path)
    subscription_id = os.getenv("SUBSCRIPTION_ID")
    resource_group_name = os.getenv("RESOURCE_GROUP_NAME")
    workspace_name = os.getenv("AML_WORKSPACE_NAME")

    # Create ML client to connect to AML workspace
    ml_client = MLClient(
        DefaultAzureCredential(
            exclude_shared_token_cache_credential=True
        ),  # Try DefaultAzureCredential(exclude_shared_token_cache_credential=True) if issues getting token locally
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
    )
    return ml_client


def main():
    args = parse_args()
    evaluation_data_start_date = args.evaluation_start_date
    evaluation_data_end_date = args.evaluation_end_date

    # compare start and end date return error if start date is greater than end date
    if evaluation_data_start_date > evaluation_data_end_date:
        raise argparse.ArgumentTypeError("Start date should be less than end date")

    endpoint_name = (
        "sample-chatbot-turn-relevance"
        if args.endpoint_name is None
        else args.endpoint_name
    )

    retry_pipeline = "false" if args.retry_pipeline is None else args.retry_pipeline

    ml_client = get_ml_client()
    job = ml_client.batch_endpoints.invoke(
        experiment_name = "sample-chatbot",
        endpoint_name=endpoint_name,
        inputs={
            "evaluation_data_start_date": Input(
                type="string", default=evaluation_data_start_date
            ),
            "evaluation_data_end_date": Input(
                type="string", default=evaluation_data_end_date
            ),
            "retry_pipeline": Input(type="string", default=retry_pipeline),
        },
    )

    ml_client.jobs.stream(name=job.name)


if __name__ == "__main__":
    main()
