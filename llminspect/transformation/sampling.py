
from logging import Logger
import pandas as pd

from llminspect.common.logger import get_logger


def simple_sample(df: pd.DataFrame, sample_conversation_fraction: float = 0.8, logger: Logger = get_logger("simple_sample")):
    """
    """
    logger.info(f"Before sampling total rows: {len(df)}")
    all_conversations = df["conversation_id"].unique()
    logger.info(f"Total conversation count: {len(all_conversations)}")
    sampled_conversations = all_conversations[:int(sample_conversation_fraction * len(all_conversations))]
    sampled_conversation_df = df[df["conversation_id"].isin(sampled_conversations)]
    logger.info(f"Sampled conversation count: {len(sampled_conversations)}")
    logger.info(f"After sampling total rows: {len(sampled_conversation_df)}")
    return sampled_conversation_df
