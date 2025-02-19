"""Unit tests for parse_score.py."""
import unittest

from parse_score import concat_results

evaluation_dataset = {
    "app_id": 1,
    "conversation_id": "convers_21",
    "metadata_id": "a64e2503-43ed-4ea6-be2c-172c75cc6af2",
    "turn_id": "1706898",
    "query": "Show me some mobiles under 50k",
    "query_time": 1706918596203,
    "response": "Here are some mobiles for you, 1. Samsung galaxy A20G, 2. Oppo 20S 5G, 3. Oneplus 10  ",
    "context": "NA",
    "response_time": 1706918596203,
    "metric_names": '[{"metric_name": "turn_relevance", "metric_version": 1.0, "metric_allowed_values": []}]',
    "evaluation_dataset_id": "eb6d7cc0-135d-409c-a209-eff8c10affb5",
}


class TestParseScore(unittest.TestCase):
    """
    Unit tests for parse_score.py.
    """

    def test_concat_results_valid_input(self):
        """
        Test that the function returns the correct final score for valid input.
        """
        evaluation_result = "5"
        # print(eval(evaluation_dataset))
        print(evaluation_dataset.keys())
        parse_score_result = concat_results(
            evaluation_dataset.copy(), evaluation_result
        )
        self.assertEqual(len(parse_score_result), 1)
        self.assertEqual(parse_score_result[0]["metric_name"], "turn_relevance")
        self.assertEqual(parse_score_result[0]["metric_value"], 5.0)
        self.assertEqual(parse_score_result[0]["metric_raw_value"], evaluation_result)

    def test_concat_results_invalid_input(self):
        """
        Test that the function returns 0 as final score for invalid input.
        """
        evaluation_result = "not a number"
        print("invalid input \n", evaluation_dataset)
        print(evaluation_dataset.keys())

        with self.assertLogs(level="ERROR") as log_context:
            parse_score_result = concat_results(
                evaluation_dataset.copy(), evaluation_result
            )

        expected_log_message = "Parsing error"
        self.assertTrue(any(expected_log_message in log for log in log_context.output))
        self.assertEqual(parse_score_result[0]["metric_name"], "turn_relevance")
        self.assertEqual(parse_score_result[0]["metric_value"], 0)
