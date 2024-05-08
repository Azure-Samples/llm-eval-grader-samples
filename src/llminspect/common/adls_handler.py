from datetime import datetime, timedelta
from typing import List
from glob import glob

import pandas as pd
from llminspect.common.logger import get_logger

logger = get_logger("adls_handler")

class ADLSHandler:
    """
    A class that provides methods for handling Azure Data Lake Storage operations.

    Methods:
        get_eval_fact_partition_paths(root_path: str, start_date: datetime, end_date: datetime) -> List[str]:
            Get the paths of the evaluation fact table partitions within the specified date range.

        read_dim_table(dim_output_path: str, dim_file_name: str) -> pd.DataFrame:
            Read a dimension table from the specified path.

        read_fact_table(fact_output_path: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
            Read the fact table from the specified output path within the specified date range.

        write_dim_table(dim_output_path: str, dim_file_name: str, df_dim_table: pd.DataFrame) -> None:
            Write the dimension table to the specified output path.

        write_fact_table(fact_output_path: str, df_fact_table: pd.DataFrame) -> None:
            Write the fact table to the specified output path in Parquet format.
    """

    def __init__(self):
        pass

    def get_eval_fact_partition_paths(self, root_path: str, start_date: datetime, end_date: datetime) -> List[str]:
        """
        Get the paths of the evaluation fact table partitions within the specified date range.

        Parameters:
            root_path (str): The root path of the evaluation fact table.
            start_date (datetime): The start date of the evaluation period.
            end_date (datetime): The end date of the evaluation period.

        Returns:
            List[str]: A list of paths of the evaluation fact table partitions.
        """
        try:
            input_paths = []
            delta = timedelta(days=1)
            while start_date <= end_date:
                year = start_date.strftime("%Y")
                month = start_date.strftime("%-m")
                day = start_date.strftime("%-d")
                path = f"{root_path}/year={year}/month={month}/day={day}/*.parquet"
                input_paths.append(path)
                start_date += delta
            logger.debug(f"Input fact table paths: {input_paths}")
            valid_paths = [f for path in input_paths for f in glob(path)]
            logger.debug(f"Reading fact table from: {valid_paths}")
            return valid_paths
        except Exception as e:
            logger.error(f"Error retrieving list of fact data files from {root_path}: {e}")
            raise e

    def read_dim_table(self, dim_output_path: str, dim_file_name: str) -> pd.DataFrame:
        """
        Read a dimension table from the specified path.

        Parameters:
            dim_output_path (str): The path to the dimension table.
            dim_file_name (str): The name of the dimension table file.

        Returns:
            pd.DataFrame: The dimension table.
        """
        try:
            df_dim_table = pd.read_parquet(f"{dim_output_path}/{dim_file_name}")
        except Exception as e:
            logger.error(f"Failed to read dim table file {dim_file_name} from {dim_output_path}: {e}")
            raise e
        return df_dim_table

    def read_fact_table(self, fact_output_path: str, start_date: datetime,
                        end_date: datetime) -> pd.DataFrame:
        """
        Read the fact table from the specified output path within the specified date range.

        Parameters:
            fact_output_path (str): The output path where the fact table is located.
            start_date (datetime): The start date of the evaluation period.
            end_date (datetime): The end date of the evaluation period.

        Returns:
            pd.DataFrame: The fact table.
        """
        try:
            valid_paths = self.get_eval_fact_partition_paths(fact_output_path, start_date, end_date)
            if len(valid_paths) == 0:
                logger.error(f"No data files found for fact table for date range {start_date} to {end_date}")
                raise FileNotFoundError(f"No data files found for fact table for date range {start_date} to {end_date}")
            df_fact_table = pd.concat([pd.read_parquet(f) for f in valid_paths])
            return df_fact_table
        except Exception as e:
            logger.error(f"Failed to read fact table from {fact_output_path}: {e}")
            raise e

    def read_task_tracker_fact_table(self, task_tracker_fact_path: str, batch_id: str) -> pd.DataFrame:
        """
        Read the fact table from the specified output path within the specified date range.

        Parameters:
            fact_output_path (str): The output path where the fact table is located.
            batch_id (str): The batch ID for the task tracker.

        Returns:
            pd.DataFrame: The fact table.
        """
        try:
            valid_paths = glob(task_tracker_fact_path+"/batch_id="+str(batch_id)+"/*.parquet")
            logger.info(f"Reading fact table from: {valid_paths}")
            if len(valid_paths) == 0:
                logger.error(f"No data files found for fact table for batch ID {batch_id}")
                raise FileNotFoundError(f"No data files found for fact table for batch ID {batch_id}")
            return pd.concat([pd.read_parquet(f) for f in valid_paths])
        except Exception as e:
            logger.error(f"Failed to read fact table from {task_tracker_fact_path}: {e}")
            raise e

    def write_dim_table(self, dim_output_path: str, dim_file_name: str, df_dim_table: pd.DataFrame, ) -> None:
        """
        Write the dimension table to the specified output path.

        Parameters:
            dim_output_path (str): The output path where the dimension table will be written.
            dim_file_name (str): The name of the dimension table file.
            df_dim_table (pd.DataFrame): The dimension table DataFrame to be written.

        Returns:
            None
        """
        try:
            df_dim_table.to_parquet(f"{dim_output_path}/{dim_file_name}", index=False)
        except Exception as e:
            logger.error(f"Failed to write dim table file {dim_file_name} to {dim_output_path}: {e}")
            raise e

    def write_fact_table(self, fact_output_path: str, df_fact_table: pd.DataFrame) -> None:
        """
        Write the fact table to the specified output path in Parquet format.

        Parameters:
            fact_output_path (str): The output path where the fact table will be written.
            df_fact_table (pd.DataFrame): The fact table DataFrame to be written.

        Returns:
            None
        """
        try:
            df_fact_table["year"] = df_fact_table["timestamp"].dt.year
            df_fact_table["month"] = df_fact_table["timestamp"].dt.month
            df_fact_table["day"] = df_fact_table["timestamp"].dt.day
            df_fact_table.to_parquet(f"{fact_output_path}", partition_cols=["year", "month", "day"], index=False)
        except Exception as e:
            logger.error(f"Failed to write fact table to {fact_output_path}: {e}")
            raise e
