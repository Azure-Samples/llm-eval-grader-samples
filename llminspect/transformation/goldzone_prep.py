from uuid import uuid4
import pandas as pd

from llminspect.common.logger import get_logger

logger = get_logger("goldzone_prep")

def _get_metadata(sampled_data: pd.DataFrame, existing_metadata: pd.DataFrame):
    """
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
    """
    df_conversation = sampled_data[['conversation_id', 'timestamp']]
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
    """
    sampled_data['metadata_id'] = sampled_data[['model', 'intent']].apply(
        tuple, 1).map(df_metadata_future.set_index(['model', 'intent'])[
        'metadata_id'])

    sampled_data["timestamp"] = pd.to_datetime(sampled_data["timestamp"])
    sampled_data['evaluation_dataset_id'] = [str(uuid4()) for _ in range(len(sampled_data.index))]

    sampled_data.drop(columns=['model', 'intent'], inplace=True)
    logger.info(f"Gold zone data columns: {sampled_data.columns}")

    if len(existing_fact_data) == 0:
        return sampled_data
    sampled_data_new = sampled_data[~sampled_data[['chatbot_name', 'conversation_id', 'metadata_id', 'turn_id']].apply(
        tuple, 1).isin(existing_fact_data[['chatbot_name', 'conversation_id', 'metadata_id', 'turn_id']].apply(tuple, 1))]
    return sampled_data_new


def create_goldzone_tables(sampled_data: pd.DataFrame, existing_fact_data: pd.DataFrame,
                           existing_metadata: pd.DataFrame, existing_conversation: pd.DataFrame):
    """
    """

    # Get the metadata
    metadata = _get_metadata(sampled_data, existing_metadata)
    # Get the conversation
    conversation = _get_conversation(sampled_data, existing_conversation)
    # Get the fact data
    fact_data = _get_fact_data(sampled_data, existing_fact_data, metadata)

    return fact_data, metadata, conversation
