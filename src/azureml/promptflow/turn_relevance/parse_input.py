from promptflow.core import tool


@tool
def parse_evaluation_data(evaluation_dataset: list):
    """
    Parse the prompt flow input and return a dictionary of the evaluation data.

    Example of prompt flow input:
    [
        {
            "evaluation_dataset_id": "",
            "app_id": "",
            "conversation_id": "",
            "metadata_id": "",
            "turn_id": "",
            "query": "",
            "query_time": "",
            "context": "",
            "response": "",
            "metric_names": ""
        }
    ]

    :param evaluation_data: Input to prompt flow.
    :return: Dictionary with evaluation data fields.
    """
    if len(evaluation_dataset) > 0:
        return evaluation_dataset[0]
    else:
        raise ValueError("Evaluation data is empty")
