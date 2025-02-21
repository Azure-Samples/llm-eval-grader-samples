# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Reusable logger for evaluation pipeline."""
import logging
import sys


def get_logger(name: str = "evaluation_pipeline", level: int = logging.INFO) -> logging.Logger:
    """Get logger for evaluation pipeline.

    Args:
        name (str, optional): Logger name. Defaults to "evaluation pipeline".
        level (int, optional): Log level. Defaults to logging.DEBUG.

    Returns:
        logging.Logger: named logger.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(handler)

    return logger