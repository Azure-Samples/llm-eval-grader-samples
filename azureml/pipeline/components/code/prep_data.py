import argparse
import json
import pandas as pd

from datetime import datetime, timedelta

from llminspect.common.adls_handler import ADLSHandler
from llminspect.common.constants import DIM_APPLICATION_PARQUET,EVALUATION_TYPE_HUMAN,EVALUATION_TYPE_LLM,EVALUATION_TYPE_BOTH
from llminspect.common.db_handler import DBHandler
from llminspect.common.logger import get_logger
from llminspect.common.utils import get_datetime_from_date_str,start_date_for_pipeline_run, end_date_for_pipeline_run

logger = get_logger("prep_data")
adls_handler = ADLSHandler()


def get_app_id_from_app_dim_table(app_dim_df, app_name, parent_app_name):
    """
    Gets the app ID from the app dimension table for an app_name.

    Returns:
        app_dim_table_path: The app dimension table path
        app_name: The app name to filter on
        parent_app_name: The parent app name to filter on
    """

    # filter app_dim_df on app_name and get the parent_app_ids
    df_filtered_on_app = app_dim_df[app_dim_df["name"].str.lower() == app_name.lower()]
    # If parent_app_id is null, set parent_app_id also as app_id
    df_filtered_on_app.loc[:, 'parent_app_id'] = df_filtered_on_app['parent_app_id'].fillna(df_filtered_on_app['app_id'])

    # create [parent_app_id, app_id] pair from app_dim_df_1
    app_id_parent_app_id_pair = df_filtered_on_app[
        ["parent_app_id", "app_id"]
    ].values.tolist()

    # go through each pair and match parent_app_name with app_name in app_dim_df
    for pair in app_id_parent_app_id_pair:
        df_filtered_on_parent_app = app_dim_df[app_dim_df["app_id"] == pair[0]]
        if df_filtered_on_parent_app["name"].iloc[0].lower() == parent_app_name.lower():
            logger.info(
                "Found app_id: %s for app_name: %s and parent_app_name: %s from DIM_APPLICATION",
                str(int(pair[1])),
                app_name,
                parent_app_name,
            )
            return str(int(pair[1]))
    return -1


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
    parser.add_argument("--parent_app_name", type=str)
    parser.add_argument("--evaluator_name", type=str)
    parser.add_argument("--metric_names", type=json.loads)
    parser.add_argument("--start_date", type=str)
    parser.add_argument("--end_date", type=str)
    parser.add_argument("--gold_zone_fact_eval_path", type=str)
    parser.add_argument("--gold_zone_dim_app_path", type=str)
    parser.add_argument("--prep_data_output_path", type=str)
    parser.add_argument("--retry_pipeline", type=str)
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


def filter_dataset_for_retry(
    key_vault_url, start_date, end_date, app_id, metric_names, eval_fact_df
):
    """
    Filter the evaluation dataset based on the metrics that are already present in the database

    Args:
        key_vault_url (str): The key vault url
        start_date (str): The start date in the format "YYYY/MM/DD HH:MM".
        end_date (str): The end date in the format "YYYY/MM/DD HH:MM".
        app_id (int): The app id
        metric_names (str): The metric names
        eval_fact_df (pandas.DataFrame): The evaluation fact DataFrame
    Returns:
        eval_fact_df (pandas.DataFrame): The filtered evaluation fact DataFrame
    """
    db_handler = DBHandler(key_vault_url)
    db_handler.init_db_connection()

    metric_ids = []
    for metric in metric_names:
        dim_metric_dict = db_handler.select_row_by_columns("DIM_METRIC", ["metric_name", "metric_version"], [metric["metric_name"], metric["metric_version"]])
        metric_id = dim_metric_dict["metric_id"]
        if metric_id is None:
            error_msg = f"Metric name {metric['metric_name']} and metric version {metric['metric_version']} not found in DIM_METRIC table"
            logger.exception(error_msg)
            raise ValueError(error_msg)
        metric_ids.append(metric_id)

    fact_input_metric_dict = db_handler.select_by_date_range_for_app_metric(
        "FACT_INPUT_DS_METRIC",
        "response_time",
        start_date,
        end_date,
        app_id,
        metric_ids,
    )
    # Filter the evaluation dataset based on the metrics that are already present in the database
    if fact_input_metric_dict is not None:
        fact_input_metric_df = pd.DataFrame(fact_input_metric_dict)
        eval_fact_df = eval_fact_df[
            ~eval_fact_df["evaluation_dataset_id"].isin(
                fact_input_metric_df["evaluation_dataset_id"]
            )
        ]
    return eval_fact_df


def filter_evaluation_fact_on_common_properties(
    eval_fact_df, app_id, start_date, end_date, metric_names
):
    """
    Filter the evaluation fact DataFrame based on common properties such as app_id, start_date, end_date, and metric_names.

    Args:
        eval_fact_df (pandas.DataFrame): The evaluation fact DataFrame.
        app_id (int): The app id to filter on.
        start_date (str): The start date in the format "YYYY/MM/DD HH:MM".
        end_date (str): The end date in the format "YYYY/MM/DD HH:MM".
        metric_names (str): The metric names to filter on.

    Returns:
        eval_fact_df (pandas.DataFrame): The filtered evaluation fact DataFrame.
    """
    eval_fact_df = eval_fact_df[eval_fact_df["is_valid_turn"].astype(str).str.lower() == "true"]
    logger.info(f"Filtered {len(eval_fact_df)} FACT_EVALUATION rows with valid turn")

    # filter eval_fact_ml_table on app_id
    eval_fact_df = eval_fact_df[eval_fact_df["app_id"].astype(str) == app_id]
    logger.info(f"Filtered {len(eval_fact_df)} FACT_EVALUATION rows for app_id: {app_id}")

    eval_fact_df["metric_names"] = json.dumps(metric_names)

    # filter eval_fact_df for start and end hour input by user
    eval_fact_df = eval_fact_df[
        (eval_fact_df["response_time"] >= start_date)
        & (eval_fact_df["response_time"] <= end_date)
    ]
    logger.info(f"Filtered {len(eval_fact_df)} FACT_EVALUATION rows for response time between {start_date} to {end_date}")
    return eval_fact_df

def filter_evaluation_fact_on_evaluation_type(eval_fact_df):
    """
    The data in the goldzone has a column called evaluation_type with values {'llm','human','both'}
    Filters out the evaluation_type = llm or both for llm evaluation

    Parameters:
    eval_fact_df (pandas.DataFrame): The DataFrame containing the evaluation data.

    Returns:
    pandas.DataFrame: The filtered DataFrame without human evaluation data, or only rows marked with llm and both
    """
    eval_fact_df = eval_fact_df[(eval_fact_df['evaluation_type'] == EVALUATION_TYPE_LLM) | (eval_fact_df['evaluation_type'] == EVALUATION_TYPE_BOTH)]
    return eval_fact_df

def format_output_based_on_evaluator(evaluator, eval_fact_df):
    """
    Format the evaluation fact dataframe which needs to be written as output based on the evaluator.
    If the evaluator is e2e_answerability, group all rows for a session into one input row for prompt flow.
    Example output for e2e_answerability:
    {"evaluation_dataset": [{eval_fact_df_row_1_for_session_1}, {eval_fact_df_row_2_for_session_1}, {eval_fact_df_row_3_for_session_1}]}
    {"evaluation_dataset": [{eval_fact_df_row_1_for_session_2}, {eval_fact_df_row_2_for_session_2}]}
    If the evaluator is not e2e_answerability, keep each row as a separate input row.
    Example output for other evaluators:
    {"evaluation_dataset": [{eval_fact_df_row_1}]}
    {"evaluation_dataset": [{eval_fact_df_row_2}]}
    {"evaluation_dataset": [{eval_fact_df_row_3}]}

    Args:
        evaluator (str): Name of the evaluation being run.
        eval_fact_df (pandas.DataFrame): The filtered evaluation fact dataframe which needs to be formatted for output.

    Returns:
        pd.DataFrame(eval_fact_formatted_dict): The formatted evaluation fact dataframe.
    """
    if evaluator == "e2e_answerability":
        eval_fact_dict = eval_fact_df.groupby('session_id').apply(lambda x: x.sort_values('transcript_turn_seq_id').to_dict('records')).tolist()
    else:
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
            "Input configuration: app_name: %s, parent_app_name: %s, evaluator_name: %s, metric_names: %s, start_date: %s, end_date: %s, gold_zone_fact_eval_path: %s, gold_zone_dim_app_path: %s, prep_data_output_path: %s, retry_pipeline: %s",
            args.app_name,
            args.parent_app_name,
            args.evaluator_name,
            args.metric_names,
            args.start_date,
            args.end_date,
            args.gold_zone_fact_eval_path,
            args.gold_zone_dim_app_path,
            args.prep_data_output_path,
            args.retry_pipeline,
        )

        # Read app dimension table
        app_dim_df = adls_handler.read_dim_table(
            args.gold_zone_dim_app_path, DIM_APPLICATION_PARQUET
        )
        logger.info(f"Read {len(app_dim_df)} rows from DIM_APPLICATION")

        # Get app_id from app_dim_table
        app_id = get_app_id_from_app_dim_table(
            app_dim_df, args.app_name, args.parent_app_name
        )

        if -1 == app_id:
            raise ValueError(
                f"Could not find app_id for app_name: {args.app_name} and parent_app_name: {args.parent_app_name} in DIM_APPLICATION"
            )
            
        start_date = start_date_for_pipeline_run(args.start_date)
        logger.info(f"Start Date is {start_date.strftime('%m/%d/%Y, %H:%M:%S')}")
        end_date =  end_date_for_pipeline_run(args.end_date)
        logger.info(f"End Date is {end_date.strftime('%m/%d/%Y, %H:%M:%S')}")
        retry_pipeline = "false" if args.retry_pipeline.strip() == "NA" else args.retry_pipeline

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
            eval_fact_df, app_id, start_date, end_date, args.metric_names
        )
        
        eval_fact_df = filter_evaluation_fact_on_evaluation_type(eval_fact_df)

        if retry_pipeline.lower() == "true":
            eval_fact_df = filter_dataset_for_retry(
                args.key_vault_url,
                start_date,
                end_date,
                app_id,
                args.metric_names,
                eval_fact_df,
            )

        if eval_fact_df.empty:
            error_msg = "Prep data returned no records to run evaluation."
            logger.error(error_msg)
            raise Exception(error_msg)

        eval_fact_df_for_write = format_output_based_on_evaluator(args.evaluator_name, eval_fact_df)

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
