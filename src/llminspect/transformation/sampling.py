
from logging import Logger
import pandas as pd

from llmevalgrader.common.logger import get_logger


def simple_sample(df: pd.DataFrame, sample_conversation_fraction: float = 0.8, logger: Logger = get_logger("simple_sample")):
    """
    Sample a fraction of conversations from a DataFrame.

    Parameters:
    - df (pd.DataFrame): The input DataFrame containing conversations.
    - sample_conversation_fraction (float): The fraction of conversations to sample. Default is 0.8.
    - logger (Logger): The logger object to log information. Default is the logger named "simple_sample".

    Returns:
    - pd.DataFrame: The sampled DataFrame containing the selected conversations.
    """
    logger.info(f"Before sampling total rows: {len(df)}")
    all_conversations = df["conversation_id"].unique()
    logger.info(f"Total conversation count: {len(all_conversations)}")
    sampled_conversations = all_conversations[:int(sample_conversation_fraction * len(all_conversations))]
    sampled_conversation_df = df[df["conversation_id"].isin(sampled_conversations)]
    logger.info(f"Sampled conversation count: {len(sampled_conversations)}")
    logger.info(f"After sampling total rows: {len(sampled_conversation_df)}")
    return sampled_conversation_df
