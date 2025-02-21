# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest import TestCase
from unittest.mock import patch
import pytest
import os
import json
from eval.end_to_end.constants import (
    CRITERIA_NAME_VAR,
    CRITERIA_PROMPT_VAR,
    CONVO_ID_VAR,
    CONVO_HISTORY_VAR,
    IDEAL_ANSWER_VAR,
    SCENARIO_ID_VAR,
    SCENARIO_DESC_VAR,
)

env_path = "eval/tests/data/dummy_env.json"
with open(env_path, "r") as f_p:
    mock_variables = json.load(f_p)
with patch.dict(os.environ, mock_variables):
    from eval.end_to_end.evaluate_conversation import (
        EndtoEndEval,
    )


class TestEvaluateObject(TestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set mock environment variables needed for each test"""
        env_path = "eval/tests/data/dummy_env.json"
        with open(env_path, "r") as f_p:
            mock_variables = json.load(f_p)

        with patch.dict(os.environ, mock_variables):
            yield

    def test_endtoend_eval(self):
        evaluator = EndtoEndEval(output_folder='fake_folder')
        fake_data = [
            {
                CONVO_ID_VAR: 0,
                "category": "Current",
                CRITERIA_NAME_VAR: "fake-name",
                CRITERIA_PROMPT_VAR: "fake-prompt",
                CONVO_HISTORY_VAR: "fake-convo",
                IDEAL_ANSWER_VAR: "fake-answer",
                SCENARIO_ID_VAR: 0,
                SCENARIO_DESC_VAR: "fake_desc",
            }
        ]
        fake_promt_dict = {"prompt": "prompt"}

        with patch(
            "eval.end_to_end.evaluate_conversation.LLMgrader"
        ) as fake_eval_class, patch(
            "eval.end_to_end.evaluate_conversation.mean"
        ) as fake_mean, patch(
            "eval.end_to_end.evaluate_conversation.mlflow"
        ) as fake_mlflow, patch(
            "eval.end_to_end.evaluate_conversation.json"
        ) as fake_json, patch(
            "eval.end_to_end.evaluate_conversation.open"
        ), patch(
            "eval.end_to_end.evaluate_conversation.os"
        ):
            fake_eval_class().validate_llm_output.return_value = {
                "0": {
                    CRITERIA_PROMPT_VAR: "fake-prompt",
                    "explanation": "some explanation",
                    "answer": "N",
                }
            }
            evaluator.evaluate_single_criterion(fake_data, fake_promt_dict)
            assert fake_eval_class().evaluate_conversation.call_count == 1
            assert fake_mean.call_count == 2
            assert fake_json.dump.call_count == 1
            assert fake_mlflow.log_metric.call_count == 1

            evaluator.evaluate_multi_criteria(fake_data, fake_promt_dict)
            assert fake_eval_class().evaluate_conversation.call_count == 2
            assert fake_mean.call_count == 4
            assert fake_json.dump.call_count == 2
            assert fake_mlflow.log_metric.call_count == 2
