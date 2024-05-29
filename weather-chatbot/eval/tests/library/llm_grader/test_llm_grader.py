import unittest
from unittest.mock import patch
import pytest

import os
import json
from eval.library.llm_grader.templates import (
    prompt_template_single_criteria_full_conversation,
)
from eval.library.llm_grader.llm_grader import LLMgrader

CONVO_ID_VAR = "convo_id"
CRITERIA_NAME_VAR = "criteria_name"
CRITERIA_PROMPT_VAR = "criteria_prompt"
CONVO_HISTORY_VAR = "message_history"
IDEAL_ANSWER_VAR = "ideal_answer"


class TestRunLocalObject(unittest.TestCase):
    @pytest.fixture(scope='module', autouse=True)
    def setup(self):
        """ Set mock environment variables needed for each test """
        env_path = 'eval/tests/data/dummy_env.json'
        with open(env_path, 'r') as f_p:
            mock_variables = json.load(f_p)

        with patch.dict(os.environ, mock_variables):
            yield

    def test_evaluate_convo(self):
        data = {
            CONVO_ID_VAR: 0,
            CRITERIA_NAME_VAR: "fake-name",
            CRITERIA_PROMPT_VAR: "fake-prompt",
            CONVO_HISTORY_VAR: "fake-convo",
            IDEAL_ANSWER_VAR: "fake-answer",
        }

        criteria = data[CRITERIA_PROMPT_VAR]
        convo = data[CONVO_HISTORY_VAR]
        with patch(
            "eval.library.llm_grader.llm_grader.get_completion"
        ) as fake_chat_class:
            evaluator = LLMgrader(
                prompt_template_single_criteria_full_conversation
            )
            evaluator.evaluate_conversation(convo, criteria)
            assert fake_chat_class.get_completion.called_once()

    def test_evaluate_completion(self):
        data = {
            CONVO_ID_VAR: 0,
            CRITERIA_NAME_VAR: "fake-name",
            CRITERIA_PROMPT_VAR: "fake-prompt",
            CONVO_HISTORY_VAR: "fake-convo",
            "completion": "fake-convo",
            IDEAL_ANSWER_VAR: "fake-answer",
        }

        criteria = data[CRITERIA_PROMPT_VAR]
        convo = data[CONVO_HISTORY_VAR]
        completion = data["completion"]
        with patch(
            "eval.library.llm_grader.llm_grader.get_completion"
        ) as fake_chat_class:
            evaluator = LLMgrader(
                prompt_template_single_criteria_full_conversation
            )
            evaluator.evaluate_conversation(convo, completion, criteria)
            assert fake_chat_class.get_completion.called_once()

    def test_validate_json(self):
        test_data = '{"some_key": "some_text"}'
        with patch(
            "eval.library.llm_grader.llm_grader.get_completion"
        ):
            evaluator = LLMgrader(
                prompt_template_single_criteria_full_conversation
            )
            answer = evaluator.validate_llm_output(test_data)
            assert answer == {'some_key': 'some_text'}
