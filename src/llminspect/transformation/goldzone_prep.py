from uuid import uuid4
import pandas as pd

from llminspect.common.logger import get_logger

logger = get_logger("goldzone_prep")

def _get_metadata(sampled_data: pd.DataFrame, existing_metadata: pd.DataFrame):
    """
    Get metadata for sampled data.

    This function takes in two dataframes: `sampled_data` and `existing_metadata`.
    It creates a new dataframe `df_metadata` with columns ['metadata_id', 'model', 'intent'].
    The function then populates the `df_metadata` dataframe with unique combinations of 'model' and 'intent' from `sampled_data`.
    Each row in `df_metadata` is assigned a unique 'metadata_id' generated using the `uuid4()` function.
    If `existing_metadata` is empty, the function returns `df_metadata`.
    Otherwise, it filters out the rows from `df_metadata` that already exist in `existing_metadata` based on 'model' and 'intent'.
    The filtered rows are then concatenated with `existing_metadata` to create `df_metadata_future`, which is returned by the function.

    Parameters:
    - sampled_data (pd.DataFrame): The dataframe containing the sampled data.
    - existing_metadata (pd.DataFrame): The dataframe containing the existing metadata.

    Returns:
    - df_metadata_future (pd.DataFrame): The dataframe containing the future metadata.

    """
    df_metadata = pd.DataFrame(columns=['metadata_id', 'model', 'intent'])
    df_metadata = sampled_data[['model', 'intent']].drop_duplicates()
    df_metadata['metadata_id'] = [str(uuid4()) for _ in range(len(df_metadata.index))]
    if len(existing_metadata) == 0:
        return df_metadata
    df_metadata_new = df_metadata[~df_metadata[['model', 'intent']]
                                  .apply(tuple,1).isin(existing_metadata[['model', 'intent']].apply(tuple,1))]
    df_metadata_future = pd.concat([existing_metadata, df_metadata_new])
    return df_metadata_future

def _get_conversation(sampled_data: pd.DataFrame, existing_conversation: pd.DataFrame):
    """
    Get the conversation data by grouping the sampled data based on conversation ID.

    Args:
        sampled_data (pd.DataFrame): The sampled data containing conversation ID and timestamp.
        existing_conversation (pd.DataFrame): The existing conversation data.

    Returns:
        pd.DataFrame: The updated conversation data.

    """
    df_conversation = sampled_data[['conversation_id', 'timestamp']]
    df_conversation = df_conversation.copy()
    df_conversation["timestamp1"] = df_conversation["timestamp"]
    df_conversation = df_conversation.groupby(['conversation_id'], group_keys=True, as_index=False).agg({'timestamp': 'min', 'timestamp1': 'max'})
    df_conversation.columns = ['conversation_id', 'conv_start_time', 'conv_end_time']
    df_conversation["conv_start_time"] = pd.to_datetime(df_conversation["conv_start_time"])
    df_conversation["conv_end_time"] = pd.to_datetime(df_conversation["conv_end_time"])

    if len(existing_conversation) == 0:
        return df_conversation
    df_conversation_new = df_conversation[~df_conversation[['conversation_id']]
                                .apply(tuple,1).isin(existing_conversation[['conversation_id']].apply(tuple,1))]
    df_conversation_future = pd.concat([existing_conversation, df_conversation_new])
    return df_conversation_future


def _get_fact_data(sampled_data: pd.DataFrame, existing_fact_data: pd.DataFrame, df_metadata_future: pd.DataFrame):
    """
    Get the fact data by processing the sampled data, existing fact data, and future metadata.

    Args:
        sampled_data (pd.DataFrame): The sampled data containing model, intent, timestamp, and other columns.
        existing_fact_data (pd.DataFrame): The existing fact data to compare with the sampled data.
        df_metadata_future (pd.DataFrame): The future metadata dataframe.

    Returns:
        pd.DataFrame: The fact data after processing.

    """
    sampled_data['metadata_id'] = sampled_data[['model', 'intent']].apply(
        tuple, 1).map(df_metadata_future.set_index(['model', 'intent'])[
        'metadata_id'])

    sampled_data["timestamp"] = pd.to_datetime(sampled_data["timestamp"])
    sampled_data['evaluation_dataset_id'] = [str(uuid4()) for _ in range(len(sampled_data.index))]
    logger.info(f"Columns in the DataFrame sampled_Data :{sampled_data.columns}")
    sampled_data.drop(columns=['model', 'intent'], inplace=True)
    logger.info(f"Gold zone data columns: {sampled_data.columns.to_list()}")

    if len(existing_fact_data) == 0:
        return sampled_data
    sampled_data_new = sampled_data[~sampled_data[['app_name', 'conversation_id', 'metadata_id', 'turn_id']].apply(
        tuple, 1).isin(existing_fact_data[['app_name', 'conversation_id', 'metadata_id', 'turn_id']].apply(tuple, 1))]
    return sampled_data_new


def create_goldzone_tables(sampled_data: pd.DataFrame, existing_fact_data: pd.DataFrame,
                           existing_metadata: pd.DataFrame, existing_conversation: pd.DataFrame):
    """
    Create goldzone tables based on the sampled data and existing data.

    Args:
        sampled_data (pd.DataFrame): The sampled data used to create the goldzone tables.
        existing_fact_data (pd.DataFrame): The existing fact data to be combined with the sampled data.
        existing_metadata (pd.DataFrame): The existing metadata to be combined with the sampled data.
        existing_conversation (pd.DataFrame): The existing conversation data to be combined with the sampled data.

    Returns:
        tuple: A tuple containing the pandas dataframes for the fact data, metadata, and conversation data.

    """
    # Get the metadata
    metadata = _get_metadata(sampled_data, existing_metadata)
    # Get the conversation
    conversation = _get_conversation(sampled_data, existing_conversation)
    # Get the fact data
    fact_data = _get_fact_data(sampled_data, existing_fact_data, metadata)

    return fact_data, metadata, conversation
