# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from typing import List

import pyodbc
from tenacity import retry, stop_after_attempt, wait_fixed

from llmevalgrader.common.get_secret import get_key_vault_secret
from llmevalgrader.common.logger import get_logger

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
