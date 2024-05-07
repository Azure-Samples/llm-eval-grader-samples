import json
from promptflow import tool
import numpy as np
import re


@tool
def concat_results(evaluation_dataset: dict, relevance_score: str):

    load_list = [{'name': 'gpt_relevance', 'score': relevance_score}]
    score_list = []
    errors = []
    for item in load_list:
        try:
            score = item["score"]
            match = re.search(r'\d', score)
            if match:
                score = match.group()
            score = float(score)
        except Exception as e:
            score = np.nan
            errors.append({"name": item["name"], "msg":   str(e), "data": item["score"]})
        score_list.append({"name": item["name"], "score": score})

    
    metrics = json.loads(evaluation_dataset["metric_names"])

    # Remove metric names dictionary, since it is flattened out in final evaluation output
    evaluation_dataset.pop("metric_names")

    evaluation_dataset["metric_name"] = metrics[0]["metric_name"]
    evaluation_dataset["metric_version"] = metrics[0]["metric_version"]
    evaluation_dataset["metric_value"] = score_list[0].get("score", np.nan)
    evaluation_dataset["metric_raw_value"] = relevance_score

    # Format the evaluation output as a list of dictionaries
    # This is the standard format for all evaluation outputs
    evaluation_output = [evaluation_dataset]
    return evaluation_output

