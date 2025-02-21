# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Contains helper functions for evaluation data"""

import pandas as pd


def append_dataset(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Helper function to append synthetic datasets together.

    Args:
        df1 (pd.DataFrame): Dataset1 with conversations and completions
        df2 (pd.DataFrame): Dataset2 with conversations and completions

    Raises:
        ValueError: Empty DataFrames Error
        ValueError: Same Columns Error

    Returns:
        pd.DataFrame: Concatenated DataFrame
    """
    if df1.empty or df2.empty:
        raise ValueError("Input DataFrames should not be empty.")

    if set(df1.columns) != set(df2.columns):
        raise ValueError("Both DataFrames should have the same columns.")

    appended_data = pd.concat([df1, df2], ignore_index=True)

    return appended_data


def get_conversation_as_string(context):
    conversation = ""
    for turn_dct in context["message_history"]:
        line = f"{turn_dct['role'].upper()}: {turn_dct['content']}"
        conversation = conversation + line + "\n"
    return conversation
