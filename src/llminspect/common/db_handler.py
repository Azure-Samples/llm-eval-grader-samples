from datetime import datetime
from typing import List

import pyodbc
from tenacity import retry, stop_after_attempt, wait_fixed

from llminspect.common.get_secret import get_key_vault_secret
from llminspect.common.logger import get_logger

logger = get_logger("db_handler")

DB_WAKEUP_RETRY_WAIT_TIME_IN_SECONDS = 10
DB_WAKEUP_ATTEMPTS = 30
DB_QUERY_TIMEOUT = 300


class DBHandler:
    """
    Class for handling database operations.
    """

    def __init__(self, key_vault_url):
        self.key_vault_url = key_vault_url
        self.conn = None

    def init_db_connection(
        self,
        server_secret_name: str = "azuresqlserver",
        database_secret_name: str = "azuresqlserver-database",
        userid_secret_name: str = "azuresqlserver-user",
        password_secret_name: str = "azuresqlserver-password",
    ):
        """Initializes the database connection."""
        try:
            server = get_key_vault_secret(self.key_vault_url, server_secret_name)
            database = get_key_vault_secret(self.key_vault_url, database_secret_name)
            userid = get_key_vault_secret(self.key_vault_url, userid_secret_name)
            password = get_key_vault_secret(self.key_vault_url, password_secret_name)

            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={userid};PWD={password}"
            self.wake_up_database(conn_str)
            logger.info(f"Connection to database {database} successful")
        except Exception as ex:
            logger.exception(f"Error connecting to database: {ex}")
            raise

    @retry(
        wait=wait_fixed(DB_WAKEUP_RETRY_WAIT_TIME_IN_SECONDS),
        stop=stop_after_attempt(DB_WAKEUP_ATTEMPTS),
    )
    def wake_up_database(self, conn_str):
        """
        Wakes up the database by executing a simple query.
        """
        logger.info("Waking up database")
        self.conn = pyodbc.connect(conn_str, timeout=DB_QUERY_TIMEOUT)
        cursor = self.conn.cursor()

        # Execute a simple query
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        logger.info("Waking up database row: %s", row)
        while row:
            row = cursor.fetchone()

    def close_db_connection(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.commit()
            self.conn.close()
            logger.info("Database connection closed")

    def _create_cursor(self):
        """
        Creates a cursor for executing SQL queries.

        Returns:
            pyodbc.Cursor: A cursor object.
        """
        return self.conn.cursor()

    def insert_into_table(self, table_name, entities):
        """
        Inserts data into the specified database table.

        Parameters:
            table_name (str): The name of the database table to insert into.
            entities (list): A list of entities that represents the data to insert.
        """
        try:
            entity = entities[0]
            columns = ", ".join(entity.__dict__.keys())
            placeholders = ", ".join("?" * len(entity.__dict__.keys()))

            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            params_list = [tuple(entity.__dict__.values()) for entity in entities]

            logger.debug(f"Running insert query: {query} with params: {params_list}")
            with self._create_cursor() as cursor:
                cursor.fast_executemany = True
                cursor.executemany(query, params_list)
                cursor.commit()
        except Exception as ex:
            logger.exception(
                f"Error inserting rows into database table {table_name}: {ex}"
            )
            raise

    def select_row_by_columns(
        self, table_name, column_names, column_values, select_column_name=None
    ):
        """
        Selects rows from the specified database table based on a given column condition.

        Parameters:
            table_name (str): The name of the database table to select from.
            column_name (str): The name of the column for the condition.
            column_value (str): The value for the condition.
            select_column_name (str): The name of the column to select. If None, selects all columns.

        Returns:
            dict or None: If select_column_name is None, a dictionary representing the selected row.
                          If select_column_name is not None, a dictionary representing the selected column.
                          None if no row is found.
        """
        try:
            if len(column_names) == 1:
                where_condition = f"{column_names[0]} = ?"
            else:
                where_condition = " AND ".join(
                    f"{column_name} = ?" for column_name in column_names
                )

            if select_column_name is None:
                query = f"SELECT * FROM {table_name} WHERE {where_condition}"
            else:
                query = f"SELECT {select_column_name} FROM {table_name} WHERE {where_condition}"

            params = tuple(column_values)

            logger.debug(f"Running select query: {query} with params: {params}")
            with self._create_cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()

                if row:
                    row_dict = dict(zip([col[0] for col in cursor.description], row))
                    if select_column_name is None:
                        return row_dict
                    else:
                        parsed_row_dict = {}
                        for key, value in row_dict.items():
                            if select_column_name in key[0]:
                                parsed_row_dict = {select_column_name: value}
                                break
                        return parsed_row_dict
                else:
                    return None
        except Exception as ex:
            logger.exception(
                f"Error fetching row(s) from database table {table_name}: {ex}"
            )
            raise

    def select_by_column_values(
        self, table_name, column_name, column_values, select_column_name=None
    ):
        """
        Selects rows from the specified database table based on a given column condition.

        Parameters:
            table_name (str): The name of the database table to select from.
            column_name (str): The name of the column for the condition.
            column_values (list): The values for the condition.
            select_column_name (str): The name of the column to select. If None, selects all columns.

        Returns:
            list: A list of dictionaries representing the selected rows.
        """
        try:
            if select_column_name is None:
                query = f'SELECT * FROM {table_name} WHERE {column_name} IN ({", ".join("?" * len(column_values))})'
            else:
                query = f'SELECT {select_column_name} FROM {table_name} WHERE {column_name} IN ({", ".join("?" * len(column_values))})'

            params = tuple(column_values)

            return self.execute_query(query, params)
        except Exception as ex:
            logger.exception(
                f"Error fetching row(s) from database table {table_name}: {ex}"
            )
            raise

    def select_by_date_range_for_app_metric(
        self, table_name, column_name, start_date, end_date, app_id, metric_ids
    ):
        """
        Selects rows from the specified database table based on a date range condition.

        Parameters:
            table_name (str): The name of the database table to select from.
            column_name (str): The name of the column for the condition.
            start_date (str): The start date for the condition.
            end_date (str): The end date for the condition.
            app_id (str): The app_id for the condition.
            metric_ids (list): The metric_ids for the condition.

        Returns:
            list: A list of dictionaries representing the selected rows.
        """
        try:
            query = f"SELECT * FROM {table_name} WHERE {column_name} >= ? AND {column_name} <= ? AND app_id = ? AND metric_id IN ({','.join('?' * len(metric_ids))})"
            params = (start_date, end_date, app_id, *metric_ids)

            return self.execute_query(query, params)
        except Exception as ex:
            logger.exception(
                f"Error fetching row(s) from database table {table_name}: {ex}"
            )
            raise

    def execute_query(self, query, params=None):
        """
        Executes a SQL query.

        Parameters:
            query (str): The SQL query to execute.
            params (tuple): A tuple of parameters for the query.
        """
        try:
            logger.debug(f"Running query: {query} with params: {params}")
            with self._create_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                rows = cursor.fetchall()
                if rows:
                    rows_dict = [
                        dict(zip([col[0] for col in cursor.description], row))
                        for row in rows
                    ]
                    return rows_dict
                else:
                    return []
        except Exception as ex:
            logger.exception(f"Error executing query: {ex}")
            raise

    def select_by_date_range(
        self,
        schema_name: str,
        table_name: str,
        date_column_name: str,
        start_date: datetime,
        end_date: datetime,
        start_page: int = None,
        page_size: int = None,
    ) -> List[dict]:
        """
        Selects rows from the specified database table based on a given date range condition.

        Parameters:
            table_name (str): The name of the database table to select from.
            date_column_name (str): The name of the column for the condition.
            start_date (datetime): The start date for the condition.
            end_date (datetime): The end date for the condition.
            start_page (int): The start page for pagination. If None, no pagination is applied.
            page_size (int): The page size for pagination. If None, no pagination is applied.

        Returns:
            list: A list of dictionaries representing the selected rows.
        """
        try:
            results = []
            sql_format_start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
            sql_format_end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")

            if start_page is not None and page_size is not None:
                end_page = start_page + page_size - 1
                query = f"SELECT * FROM \
                            ( \
                            SELECT *, Row_number() over (order by {date_column_name} desc) as rownumber \
                                FROM [{schema_name}].[{table_name}] \
                                    WHERE {date_column_name} BETWEEN '{sql_format_start_date}' AND '{sql_format_end_date}' \
                            )tbl \
                            where rownumber between {start_page} and {end_page}"

            else:
                query = f"SELECT * FROM {table_name} \
                            WHERE {date_column_name} BETWEEN '{sql_format_start_date}' AND '{sql_format_end_date}' \
                            ORDER BY {date_column_name}"

            logger.debug(f"Running select query: {query}")
            with self._create_cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        results.append(row_dict)
                return results
        except Exception as ex:
            logger.exception(
                f"Error fetching row(s) from database table {table_name}: {ex}"
            )
            raise ex

    def upsert_into_table(
        self, table_name, entities, unique_columns, is_insert_only=False
    ):
        """
        Upserts data into the specified database table.

        Parameters:
            table_name (str): The name of the database table to upsert into.
            entities (list): A list of entities that represents the data to upsert.
            unique_columns (list): A list of column names where date is unique
        """
        logger.debug("DB Handler : Upsert")
        if entities is not None and len(entities) > 0:
            entity = entities[0]
            columns = ", ".join(entity.__dict__.keys())
            placeholders = ", ".join("?" * len(entity.__dict__.keys()))
            try:
                query = ""
                if is_insert_only:
                    query = f"MERGE {table_name} AS target \
                            USING (VALUES ( {','.join(['?']*len(unique_columns))})) AS source ({','.join(unique_columns)}) \
                            ON ({' AND '.join([f'target.{col} = source.{col}' for col in unique_columns])}) \
                            WHEN NOT MATCHED THEN \
                            INSERT ({columns}) VALUES ({placeholders});"
                else:
                    query = f"MERGE {table_name} AS target \
                            USING (VALUES ( {','.join(['?']*len(unique_columns))})) AS source ({','.join(unique_columns)}) \
                            ON ({' AND '.join([f'target.{col} = source.{col}' for col in unique_columns])}) \
                            WHEN MATCHED THEN \
                            UPDATE SET {','.join(column + ' = ?' for column in entity.__dict__.keys())} \
                            WHEN NOT MATCHED THEN \
                            INSERT ({columns}) VALUES ({placeholders});"

                logger.info(f"length of entities to be upserted: {len(entities)}")
                params_list = []
                for entiy in entities:
                    unique_values = tuple(entiy.__dict__[col] for col in unique_columns)
                    placeholder_values = tuple(entiy.__dict__.values())
                    merge_params = (
                        tuple(unique_values + placeholder_values)
                        if is_insert_only
                        else tuple(
                            unique_values + placeholder_values + placeholder_values
                        )
                    )
                    params_list.append(merge_params)
                logger.debug(f"length of params to be upserted: {len(params_list)}")
                with self._create_cursor() as cursor:
                    cursor.fast_executemany = True
                    cursor.executemany(query, params_list)
                    cursor.commit()
            except Exception as ex:
                logger.exception(
                    f"Error inserting rows into database table {table_name}: {ex}"
                )
                raise

    def fetch_latest_date_from_fact(self, source, source_schema, source_table):
        """
            Fetches the latest date from the specified fact table.

            Args:
                source (str): The data source name.
                source_schema (str): The schema name of the source table.
                source_table (str): The name of the source table.

            Returns:
                str: The latest date from the fact table in the format "YYYY/MM/DD".
            """
        latest_date = None
        try:
            timestamp_column = "time_stamp_request"
            if source.lower() == "fdp":
                self.init_db_connection(
                    server_secret_name="fdp-azuresqlserver",
                    database_secret_name="fdp-azuresqlserver-database",
                    userid_secret_name="fdp-azuresqlserver-user",
                    password_secret_name="fdp-azuresqlserver-password",
                        )
            else:
                self.init_db_connection()
            query = f"""
                    SELECT MAX({timestamp_column}) as latest_date
                    FROM {source_schema}.{source_table}
                """
            result = self.execute_query(query)
            latest_date = result[0]["latest_date"].strftime("%Y/%m/%d")
            logger.info(f"Latest date from fact table: {latest_date}")
        except Exception as e:
            logger.error(
                f"Unable to fetch latest date from fact table: {source_schema}.{source_table}: {e}"
            )
            raise e
        finally:
            self.close_db_connection()
        return latest_date
    
    def select_by_date_range_for_human_eval(
        self,
        table_name: str,
        start_date: datetime,
        end_date: datetime,
        start_date_column_name: str,
        end_date_column_name: str,
        project_id: str,
        batch_status: list
    ) -> List[dict]:
        """
        Selects rows from the specified database table based on a given date range condition.

        Parameters:
            table_name (str): The name of the database table to select from.
            start_date (datetime): The start date for the condition.
            end_date (datetime): The end date for the condition.
            start_date_column_name (str): The name of the column for the start date condition.
            end_date_column_name (str): The name of the column for the end date condition.
            project_id (str): The project_id for the batch.
            batch_status (list): The list of batch status to filter the rows.

        Returns:
            list: A list of dictionaries representing the selected rows.
        """
        try:
            results = []
            
            status_values = ", ".join([f"'{value}'" for value in batch_status])
            
            query = f"SELECT * FROM {table_name} \
                      WHERE {start_date_column_name} = '{start_date}' \
                      AND  {end_date_column_name} = '{end_date}'\
                      AND project_id = '{project_id}'\
                      AND client_status IN ({status_values})"

            logger.debug(f"Running select query: {query}")
            with self._create_cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        results.append(row_dict)
                return results
        except Exception as ex:
            logger.exception(
                f"Error fetching row(s) from database table {table_name}: {ex}"
            )
            raise ex
