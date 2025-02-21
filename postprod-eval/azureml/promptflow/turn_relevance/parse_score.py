# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import logging
import re

import numpy as np

from promptflow.core import tool


@tool
def concat_results(evaluation_dataset: dict, relevance_score: str):
    """Parse the results of the evaluation score for Turn Relevance.

    Args:
        evaluation_dataset (dict): The evaluation dataset.
        relevance_score (str): The evaluation result LLM provides, possibly
                               contains values from 1 to 5.

    Returns:
        evaluation_output (list): The parsed results of the evaluation score appended to the original evaluation dataset.
    """

    load_list = [{"name": "gpt_relevance", "score": relevance_score}]
    score_list = []
    errors = []
    for item in load_list:
        try:
            score = item["score"]
            match = re.search(r"\d", score)
            if match:
                score = match.group()
            score = float(score)
        except Exception as e:
            logging.error("Parsing error: %s", e)
            score = 0
            errors.append({"name": item["name"], "msg": str(e), "data": item["score"]})
        score_list.append({"name": item["name"], "score": score})

    metrics = json.loads(evaluation_dataset["metric_names"])

    # Remove metric names dictionary, since it is flattened out in final evaluation output
    evaluation_dataset.pop("metric_names")

    evaluation_dataset["metric_name"] = metrics[0]["metric_name"]
    evaluation_dataset["metric_version"] = metrics[0]["metric_version"]
    evaluation_dataset["metric_value"] = score_list[0].get("score", 0)
    evaluation_dataset["metric_raw_value"] = relevance_score
    evaluation_dataset["metric_type"] = "numerical"

    # Format the evaluation output as a list of dictionaries
    # This is the standard format for all evaluation outputs
    evaluation_output = [evaluation_dataset]
    logging.info("Evaluation output: %s", evaluation_output)
    return evaluation_output
