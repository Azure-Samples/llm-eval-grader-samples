import argparse
import os
import pandas as pd
from pathlib import Path
import datetime

from llminspect.common.entities import FactEvaluationMetric, DimMetrics
from llminspect.common.db_handler import DBHandler
from llminspect.common.logger import get_logger
from llminspect.common.mlflow_logger import mlflow_log_metric

logger = get_logger("write_metrics")

class MetricsProcessor:
    """
    Class for processing and writing evaluation metrics to a database table.
    """
    def __init__(self, key_vault_url):
        self.db_handler = DBHandler(key_vault_url)
        self.db_handler.init_db_connection()

    def read_metrics(self, eval_dataset_path, eval_metrics_data_path):
        """
        Reads evaluation metrics data from promptflow output files.

        Parameters:
            eval_dataset_path (str): Path to the promptflow input files containing evaluation dataset.
            eval_metrics_data_path (str): Path to the promptflow output files containing evaluation metrics.

        Returns:
            list: A list of dictionaries representing the raw evaluation metrics data.
        """
        pf_output_files_list = os.listdir(eval_metrics_data_path)
        eval_metric_raw_data = []
        pf_output_row_count = 0
        for pf_output_file in pf_output_files_list:
            with open((Path(eval_metrics_data_path)/pf_output_file), 'r') as file:
                eval_metrics_df = pd.read_json(file, lines=True)
                eval_metrics_df = eval_metrics_df.fillna(value=0)
                pf_output_row_count += eval_metrics_df.shape[0]
                for _, row in eval_metrics_df.iterrows():
                    for eval_metrics_row in row["evaluation_results"]:
                        eval_metric_raw_data.append(eval_metrics_row)

        pf_input_files_list = os.listdir(eval_dataset_path)
        pf_input_row_count = 0
        for pf_input_file in pf_input_files_list:
            with open((Path(eval_dataset_path)/pf_input_file), 'r') as file:
                pf_input_df = pd.read_json(file, lines=True)
                pf_input_row_count = pf_input_df.shape[0]

        mlflow_log_metric("evaluation_input_rows", pf_input_row_count)
        mlflow_log_metric("evaluation_successful_rows", pf_output_row_count)
        mlflow_log_metric("evaluation_failed_rows", pf_input_row_count - pf_output_row_count)
        logger.info(f"Read {pf_output_row_count} rows from prompt flow output files.")
        if pf_input_row_count != pf_output_row_count:
            logger.error(f"Prompt flow input and output row counts do not match. Input: {pf_input_row_count} row(s), Output: {pf_output_row_count} row(s)")
            logger.error("Please check pipeline job logs for failed mini-batches.")
        return eval_metric_raw_data

    def process_metrics(self, eval_metrics_raw_data):
        """
        Processes raw evaluation metrics data and transforms it into FactInputDSMetric entities.

        Parameters:
            eval_metrics_raw_data (list): A list of dictionaries representing raw evaluation metrics data.

        Returns:
            list: A list of FactInputDSMetric entities.
        """
        fact_evaluation_metric_list = []
        logger.info("Processing raw evaluation metrics data")
        for eval_metrics_row in eval_metrics_raw_data:
            dim_metric_dict = self.db_handler.select_row_by_columns("DIM_METRIC", ["metric_name", "metric_version"], [eval_metrics_row["metric_name"], str(eval_metrics_row["metric_version"])])

            if dim_metric_dict is None or dim_metric_dict["metric_id"] is None:
                logger.info(f"Metric name {eval_metrics_row['metric_name']} not found in DIM_METRIC table. Adding metric to DIM_METRIC table...")
                unique_columns = {"metric_name", "metric_version"}
                dim_metric = DimMetrics(
                    metric_name=eval_metrics_row["metric_name"],
                    metric_version=eval_metrics_row["metric_version"],
                    metric_type=eval_metrics_row["metric_type"],
                    evaluator_name=eval_metrics_row["metric_name"],
                    evaluator_type="llm", # TODO: Change to evaluator_type from promptflow output
                    created_by="system",
                    updated_date=datetime.datetime.now(),
                    updated_by="system",
                )
                self.db_handler.upsert_into_table(
                    "DIM_METRIC",
                    [dim_metric],
                    unique_columns,
                    True,
                )
                logger.info("Upsertion into DIM_METRICS table complete.")
                dim_metric_dict = self.db_handler.select_row_by_columns("DIM_METRIC", ["metric_name", "metric_version"], [eval_metrics_row["metric_name"], eval_metrics_row["metric_version"]])
                metric_id = dim_metric_dict["metric_id"]
                if metric_id is None:
                    error_msg = f"Metric name {eval_metrics_row['metric_name']} not found in DIM_METRIC table after upsertion"
                    logger.exception(error_msg)
                    raise ValueError(error_msg)
            else:
                metric_id = dim_metric_dict["metric_id"]
                if metric_id is None:
                    error_msg = f"Metric name {eval_metrics_row['metric_name']} not found in DIM_METRIC table"
                    logger.exception(error_msg)
                    raise ValueError(error_msg)
            
            metric_type = dim_metric_dict["metric_type"]
            if metric_type is None:
                error_msg = f"Metric type for metric name {eval_metrics_row['metric_name']} not found in DIM_METRIC table"
                logger.exception(error_msg)
                raise ValueError(error_msg)

            if str(metric_type).lower() == "numerical":
                metric_numeric_value = float(eval_metrics_row["metric_value"])
                metric_str_value = None
            elif str(metric_type).lower() == "categorical":
                metric_numeric_value = None
                metric_str_value = eval_metrics_row["metric_value"]
            else:
                error_msg = f"Invalid metric type {metric_type}. Allowed values are 'numerical' and 'categorical'"
                logger.exception(error_msg)
                raise ValueError(error_msg)
            
            fact_evaluation_metric = FactEvaluationMetric(
                metric_id=metric_id,
                evaluation_dataset_id=eval_metrics_row["evaluation_dataset_id"],
                conversation_id=eval_metrics_row["conversation_id"],
                metadata_id=eval_metrics_row["metadata_id"],
                evaluator_metadata=None,
                metric_numeric_value=metric_numeric_value,
                metric_str_value=metric_str_value,
                metric_raw_value=eval_metrics_row["metric_raw_value"],
                fact_creation_time=datetime.datetime.fromtimestamp(eval_metrics_row["timestamp"]/1000).strftime("%Y-%m-%d %H:%M:%S"),
                created_by="system",
                updated_date=datetime.datetime.now(),
                updated_by="system"          
            )
            fact_evaluation_metric_list.append(fact_evaluation_metric)
        logger.info(f"Transformed {len(fact_evaluation_metric_list)} prompt flow output rows into FACT_EVALUATION_METRIC rows.")
        return fact_evaluation_metric_list
    
    def write_metrics(self, fact_evaluation_metric_list):
        """
        Writes FactInputDSMetric entities to database table.

        Parameters:
            fact_evaluation_metric_list (list): A list of FactInputDSMetric entities.
        """
        logger.info(f"Inserting {len(fact_evaluation_metric_list)} rows into FACT_EVALUATION_METRIC table...")
        unique_columns = {"evaluation_dataset_id", "metric_id"}
        self.db_handler.upsert_into_table("FACT_EVALUATION_METRIC", fact_evaluation_metric_list, unique_columns, True)
        logger.info("Insertion into FACT_EVALUATION_METRIC table complete.")
    
    def close_connection(self):
        """
        Closes the database connection.
        """
        self.db_handler.close_db_connection()


def parse_args():
    """
    Parses the user arguments.

    Returns:
        argparse.Namespace: The parsed user arguments.
    """
    parser = argparse.ArgumentParser(
        allow_abbrev=False, description="parse user arguments"
    )
    parser.add_argument("--eval_dataset_path", type=str, help="Path to prep data output containing evaluation dataset")
    parser.add_argument("--eval_metrics_data_path", type=str, help="Path to promptflow output containing evaluation metrics")
    parser.add_argument("--key_vault_url", type=str, help="Key vault url")
    args, _ = parser.parse_known_args()
    return args                

def main():
    args = parse_args()

    metrics_processor = MetricsProcessor(args.key_vault_url)

    eval_metrics_raw_data = metrics_processor.read_metrics(args.eval_dataset_path, args.eval_metrics_data_path)
    fact_evaluation_metric_list = metrics_processor.process_metrics(eval_metrics_raw_data)
    metrics_processor.write_metrics(fact_evaluation_metric_list)
    metrics_processor.close_connection()

if __name__ == "__main__":
    main()
