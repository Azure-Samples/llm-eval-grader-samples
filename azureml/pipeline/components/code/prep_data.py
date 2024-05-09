import argparse
import json
import pandas as pd

from datetime import datetime

from llminspect.common.adls_handler import ADLSHandler
from llminspect.common.db_handler import DBHandler
from llminspect.common.logger import get_logger
from llminspect.common.utils import start_date_for_pipeline_run, end_date_for_pipeline_run

logger = get_logger("prep_data")
adls_handler = ADLSHandler()


def parse_args():
    """
    Parses the user arguments.

    Returns:
        argparse.Namespace: The parsed user arguments.
    """
    parser = argparse.ArgumentParser(
        allow_abbrev=False, description="parse user arguments"
    )
    parser.add_argument("--app_name", type=str)
    parser.add_argument("--app_type", type=str)
    parser.add_argument("--evaluator_name", type=str)
    parser.add_argument("--metric_names", type=json.loads)
    parser.add_argument("--start_date", type=str)
    parser.add_argument("--end_date", type=str)
    parser.add_argument("--gold_zone_fact_eval_path", type=str)
    parser.add_argument("--prep_data_output_path", type=str)
    parser.add_argument("--key_vault_url", type=str)    

    args, _ = parser.parse_known_args()
    return args


def write_filtered_parquet_to_evaluation_zone(eval_fact_df, output_path):
    """
    Writes the filtered DataFrame to the evaluation zone as a parquet file.

    Args:
        eval_fact_df (pandas.DataFrame): The filtered DataFrame.

    Returns:
        None
    """
    datetime_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    # write eval_fact_df to a json lines file
    eval_fact_df.to_json(
        f"{output_path}/evaluation_fact_{datetime_suffix}.jsonl", orient="records", lines=True
    )

    return

def filter_evaluation_fact_on_common_properties(
    eval_fact_df, app_name, app_type, start_date, end_date, metric_names
):
    """
    Filter the evaluation fact DataFrame based on common properties such as app_name, start_date, end_date, and metric_names.

    Args:
        eval_fact_df (pandas.DataFrame): The evaluation fact DataFrame.
        app_name (str): The app name to filter on.
        app_type (str): The app type to filter on.
        start_date (str): The start date in the format "YYYY/MM/DD HH:MM".
        end_date (str): The end date in the format "YYYY/MM/DD HH:MM".
        metric_names (str): The metric names to filter on.

    Returns:
        eval_fact_df (pandas.DataFrame): The filtered evaluation fact DataFrame.
    """

    # filter eval_fact_ml_table on app_name and app_type
    eval_fact_df = eval_fact_df[eval_fact_df["app_name"] == app_name]
    eval_fact_df = eval_fact_df[eval_fact_df["app_type"] == app_type]
    
    eval_fact_df = eval_fact_df[eval_fact_df["app_name"] == app_name]
    logger.info(f"Filtered {len(eval_fact_df)} FACT_EVALUATION rows for app_id: {app_name}")

    eval_fact_df["metric_names"] = json.dumps(metric_names)

    # filter eval_fact_df for start and end hour input by user
    #convert start_date and end_date to datetime64[ns, UTC]
    eval_fact_df = eval_fact_df[
        (eval_fact_df["timestamp"] >= pd.to_datetime(start_date, utc=True))
        & (eval_fact_df["timestamp"] <= pd.to_datetime(end_date, utc=True))
    ]
    logger.info(f"Filtered {len(eval_fact_df)} FACT_EVALUATION rows for time between {start_date} to {end_date}")
    return eval_fact_df


def format_dataframe_output(eval_fact_df):
    """
    Format the evaluation fact dataframe which needs to be written as output based on the evaluator.

    Example output for default evaluators:
    {"evaluation_dataset": [{eval_fact_df_row_1}]}
    {"evaluation_dataset": [{eval_fact_df_row_2}]}
    {"evaluation_dataset": [{eval_fact_df_row_3}]}

    Args:
        evaluator (str): Name of the evaluation being run.
        eval_fact_df (pandas.DataFrame): The filtered evaluation fact dataframe which needs to be formatted for output.

    Returns:
        pd.DataFrame(eval_fact_formatted_dict): The formatted evaluation fact dataframe.
    """

    eval_fact_dict = [[row.to_dict()] for _, row in eval_fact_df.iterrows()]
    
    eval_fact_formatted_dict = [{"evaluation_dataset": item} for item in eval_fact_dict]

    return pd.DataFrame(eval_fact_formatted_dict)  
      
def main():
    """
    The main function that orchestrates the data preparation process.
    """
    try:
        args = parse_args()
        logger.debug(
            "Input configuration: app_name: %s, evaluator_name: %s, metric_names: %s, start_date: %s, end_date: %s, gold_zone_fact_eval_path: %s, prep_data_output_path: %s",
            args.app_name,
            args.evaluator_name,
            args.metric_names,
            args.start_date,
            args.end_date,
            args.gold_zone_fact_eval_path,
            args.prep_data_output_path,
        )
            
        start_date = start_date_for_pipeline_run(args.start_date)
        logger.info(f"Start Date is {start_date.strftime('%m/%d/%Y, %H:%M:%S')}")
        end_date =  end_date_for_pipeline_run(args.end_date)
        logger.info(f"End Date is {end_date.strftime('%m/%d/%Y, %H:%M:%S')}")

        try:
            eval_fact_df = adls_handler.read_fact_table(
                args.gold_zone_fact_eval_path,
                start_date,
                end_date,
            )
            logger.info(f"Read {len(eval_fact_df)} rows from FACT_EVALUATION for date range {start_date} to {end_date}")
        except Exception as e:
            logger.error(f"Failed to read FACT_EVALUATION data for date range {start_date} to {end_date}: {e}")
            raise e

        eval_fact_df = filter_evaluation_fact_on_common_properties(
            eval_fact_df, args.app_name, args.app_type, start_date, end_date, args.metric_names
        )

        if eval_fact_df.empty:
            error_msg = "Prep data returned no records to run evaluation."
            logger.error(error_msg)
            raise Exception(error_msg)

        eval_fact_df_for_write = format_dataframe_output(eval_fact_df)

        write_filtered_parquet_to_evaluation_zone(
            eval_fact_df_for_write, args.prep_data_output_path
        )
        logger.info("Saved filtered parquet file to evaluation zone")

    except Exception as e:
        logger.error(f"Failed to prepare data for evaluation: {e}")
        raise e

    return


if __name__ == "__main__":
    main()
