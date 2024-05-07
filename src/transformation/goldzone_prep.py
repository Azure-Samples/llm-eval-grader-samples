from uuid import uuid4
import pandas as pd
import numpy as np
from common.logger import get_logger
from datetime import datetime

logger = get_logger("goldzone_prep")

def get_metadata(sampled_data: pd.DataFrame, existing_metadata: pd.DataFrame):
    """
    Generates metadata for sampled data by combining it with existing metadata.

    Args:
        sampled_data (pd.DataFrame): DataFrame containing sampled data.
        existing_metadata (pd.DataFrame): DataFrame containing existing metadata.

    Returns:
        pd.DataFrame: DataFrame containing the combined metadata.
    """
    df_metadata = pd.DataFrame(columns=['metadata_id', 'business_unit', 'super_category', 'vertical', 'pid'])
    df_metadata = sampled_data[['business_unit', 'super_category', 'vertical', 'pid']].drop_duplicates()
    df_metadata['metadata_id'] = [str(uuid4()) for _ in range(len(df_metadata.index))]
    if len(existing_metadata) == 0:
        return df_metadata
    df_metadata_new = df_metadata[~df_metadata[['business_unit', 'super_category', 'vertical', 'pid']]
                                  .apply(tuple,1).isin(existing_metadata[['business_unit', 'super_category', 'vertical', 'pid']].apply(tuple,1))]
    df_metadata_future = pd.concat([existing_metadata, df_metadata_new])
    return df_metadata_future

def get_router_function_data(sampled_data: pd.DataFrame, existing_router_function_data: pd.DataFrame):
    """
    Generates Router Function data for sampled data by combining it with existing router function data.

    Args:
        sampled_data (pd.DataFrame): DataFrame containing sampled data.
        existing_metadata (pd.DataFrame): DataFrame containing existing router function data.

    Returns:
        pd.DataFrame: DataFrame containing the combined metadata.
    """
    df_router_function = pd.DataFrame(columns=['router_function'])
    df_router_function = sampled_data[['router_function']].drop_duplicates()
    df_router_function['router_function_id'] = [str(uuid4()) for _ in range(len(df_router_function.index))]
    if len(existing_router_function_data) == 0:
        return df_router_function
    df_router_function_new = df_router_function[~df_router_function[['router_function']]
                                  .apply(tuple,1).isin(existing_router_function_data[['router_function']].apply(tuple,1))]
    df_router_function_future = pd.concat([existing_router_function_data, df_router_function_new])
    return df_router_function_future

def get_session(sampled_data: pd.DataFrame, existing_session: pd.DataFrame):
    """
    Get the session information from sampled data and existing session data.

    Args:
        sampled_data (pd.DataFrame): DataFrame containing sampled data.
        existing_session (pd.DataFrame): DataFrame containing existing session data.

    Returns:
        pd.DataFrame: DataFrame containing the updated session data.
    """
    df_session = sampled_data[['session_id', 'conversation_id', 'query_time', 'response_time']]
    if 'query_time' not in sampled_data.columns:
        sampled_data['query_time'] = pd.to_datetime(sampled_data['response_time'])
    df_session = df_session.groupby(['session_id', 'conversation_id'], group_keys=True, as_index=False).agg({'query_time': 'min', 'response_time': 'max'})

    df_session.columns = ['session_id', 'conversation_id', 'start_time', 'end_time']
    df_session["start_time"] = df_session["start_time"].apply(lambda x: datetime.fromtimestamp(x/1000000000.0) if isinstance(x, int) else x)
    df_session["end_time"] = df_session["end_time"].apply(lambda x: datetime.fromtimestamp(x/1000000000.0) if isinstance(x, int) else x)
    df_session["start_time"] = pd.to_datetime(df_session["start_time"])
    df_session["end_time"] = pd.to_datetime(df_session["end_time"])

    if len(existing_session) == 0:
        return df_session
    df_session_new = df_session[~df_session[['session_id', 'conversation_id']]
                                .apply(tuple,1).isin(existing_session[['session_id', 'conversation_id']].apply(tuple,1))]
    df_session_future = pd.concat([existing_session, df_session_new])
    return df_session_future


def get_fact_data(sampled_data: pd.DataFrame, existing_fact_data: pd.DataFrame,
                  df_metadata_future: pd.DataFrame, existing_app: pd.DataFrame, future_router_function: pd.DataFrame):
    """
    Retrieves fact data based on the provided parameters.

    Args:
        sampled_data (pd.DataFrame): The sampled data.
        existing_fact_data (pd.DataFrame): The existing fact data.
        df_metadata_future (pd.DataFrame): The future metadata.
        existing_app (pd.DataFrame): The existing app data.
        future_router_function (pd.DataFrame): The future router function data.

    Returns:
        pd.DataFrame: The retrieved fact data.
    """
    sampled_data['metadata_id'] = sampled_data[['business_unit', 'super_category', 'vertical', 'pid']].apply(
        tuple, 1).map(df_metadata_future.set_index(['business_unit', 'super_category', 'vertical', 'pid'])[
        'metadata_id'])

    sampled_data['app_id'] = sampled_data[['app_name', 'app_type']].apply(tuple, 1).map(
        existing_app.set_index(['name', 'type'])['app_id'])
    if sampled_data['app_id'].isnull().any():
        logger.info(f"Existing app data {existing_app[['name', 'type']]}")
        logger.error(f"App name and type combination not found in existing app data. App name: {sampled_data['app_name'].unique()}, App type: {sampled_data['app_type'].unique()}")
        raise Exception("App name and type combination not found in existing app data. Please onboard the app first and then rerun the transformation pipeline.")

    if 'router_function' not in sampled_data.columns:
        sampled_data['router_function'] = 'NA'
    sampled_data['router_function_id'] = sampled_data['router_function'].map(
        future_router_function.set_index('router_function')['router_function_id'])


    if 'query_time' not in sampled_data.columns:
        sampled_data['query_time'] = pd.to_datetime(sampled_data['response_time'])
    sampled_data["query_time"] = sampled_data["query_time"].apply(lambda x: datetime.fromtimestamp(x/1000000000.0) if isinstance(x, int) else x)
    sampled_data["response_time"] = sampled_data["response_time"].apply(lambda x: datetime.fromtimestamp(x/1000000000.0) if isinstance(x, int) else x)
    sampled_data["query_time"] = pd.to_datetime(sampled_data["query_time"])
    sampled_data["response_time"] = pd.to_datetime(sampled_data["response_time"])
    sampled_data['evaluation_dataset_id'] = [str(uuid4()) for _ in range(len(sampled_data.index))]

    sampled_data.drop(columns=[
        'business_unit', 'super_category', 'vertical', 'pid',
        'app_name', 'app_type',
        'conversation_id',
        'router_function',
        ], inplace=True)
    logger.info(f"Gold zone data columns: {sampled_data.columns}")

    if len(existing_fact_data) == 0:
        return sampled_data
    sampled_data_new = sampled_data[~sampled_data[['app_id', 'session_id', 'metadata_id', 'transcript_id']].apply(
        tuple, 1).isin(existing_fact_data[['app_id', 'session_id', 'metadata_id', 'transcript_id']].apply(tuple, 1))]
    return sampled_data_new


def create_goldzone_tables(sampled_data: pd.DataFrame, existing_fact_data: pd.DataFrame,
                           existing_metadata: pd.DataFrame, existing_session: pd.DataFrame,
                           existing_app: pd.DataFrame, existing_router_function: pd.DataFrame):
    """
    Create the Goldzone tables.

    Args:
        sampled_data (pd.DataFrame): The sampled DataFrame.
        existing_fact_data (pd.DataFrame): The existing fact data.
        existing_metadata (pd.DataFrame): The existing metadata.
        existing_session (pd.DataFrame): The existing session.
        existing_app (pd.DataFrame): The existing app.
        existing_router_function (pd.DataFrame): The existing router function.


    Returns:
        pd.DataFrame: The fact data.
        pd.DataFrame: The metadata.
        pd.DataFrame: The session.
        pd.DataFrame: The Router Function data.
    """

    # Get the metadata
    metadata = get_metadata(sampled_data, existing_metadata)
    # Get the session
    session = get_session(sampled_data, existing_session)
    # Get Router Function data
    router_function_data = get_router_function_data(sampled_data, existing_router_function)
    # Get the fact data
    fact_data = get_fact_data(sampled_data, existing_fact_data, metadata, existing_app, router_function_data)

    return fact_data, metadata, session, router_function_data
