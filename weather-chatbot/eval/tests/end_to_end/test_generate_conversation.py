import unittest
from unittest.mock import patch, MagicMock
import pytest
import os
import json
import pandas as pd

from eval.end_to_end.generate_conversation import (
    OrchestrateConversation,
    CONVO_DATA_FILE_NAME,
    CONVO_RUNTIME_FILE_NAME,
)
from eval.end_to_end.constants import (
    CONVO_HISTORY_VAR,
    CONVO_ID_VAR,
    SCENARIO_DESC_VAR,
    SCENARIO_ID_VAR
)


class TestRunLocalObject(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set mock environment variables needed for each test"""
        env_path = "eval/tests/data/dummy_env.json"
        with open(env_path, "r") as f_p:
            mock_variables = json.load(f_p)

        with patch.dict(os.environ, mock_variables):
            yield

    def test_initialize_scenario_criteria_df(self):
        """test initialize_scenario_criteria_df function"""
        fake_cg = MagicMock()
        orch_convo = OrchestrateConversation(fake_cg)
        df = orch_convo.initialize_scenario_criteria_df()
        assert isinstance(df, pd.DataFrame)
        with patch(
            "eval.end_to_end.generate_conversation.pd"
        ) as fake_pd:
            fake_df = MagicMock()
            fake_pd.read_csv.return_value = fake_df
            orch_convo.initialize_scenario_criteria_df()
            assert fake_df.user_prompt.fillna.called_with('')
            assert fake_df.profile_overrides.fillna.called_with('')

    def test_generate_structured_convo_data_per_scenario(self):
        """test generate_structured_convo_data_per_scenario function"""
        group = ("some_desc", '{"some_dict": "some"}', "some_prompt")
        df = pd.read_csv("eval/tests/data/dummy_scenario.csv")

        fake_cg = MagicMock()
        fake_func = MagicMock()
        fake_func.return_value = [{"some_key": "some_value"}]
        orch_convo = OrchestrateConversation(fake_cg)
        fake_cg.assess_conversation.side_effect = [{"answer": "N"}, {"answer": "Y"}]
        orch_convo.generate_scenario_convo_dict_helper = fake_func
        with patch(
            "eval.end_to_end.generate_conversation.StandardUserGenerator"
        ) as fake_cust_gen:
            orch_convo.generate_structured_convo_data_per_scenario(group, df)
            assert fake_cg.assess_conversation.call_count == 0
            assert fake_cust_gen.called

    def test_generate_structured_convo_data_list(self):
        """test generate_structured_convo_data_list function"""
        fake_cg = MagicMock()
        orch_convo = OrchestrateConversation(fake_cg)
        df = pd.read_csv("eval/tests/data/dummy_scenario.csv")
        df["num_convo_to_generate"] = df["num_convo_to_generate"].fillna(0)
        df.profile_overrides = df.profile_overrides.fillna('')
        df.user_prompt = df.user_prompt.fillna('')

        fake_funk = MagicMock()
        fake_funk.return_value = df
        orch_convo.initialize_scenario_criteria_df = fake_funk
        orch_convo.generate_structured_convo_data_per_scenario = MagicMock()
        with patch(
            "eval.end_to_end.generate_conversation.time.time"
        ) as fake_time:
            orch_convo.generate_structured_convo_data_list()
            assert orch_convo.generate_structured_convo_data_per_scenario.call_count == 3
            assert fake_time.called
            assert fake_time.call_count == 2

    def test_generate_scenario_convo_dict_helper(self):
        """test generate_scenario_convo_dict_helper function"""
        with patch('eval.end_to_end.generate_conversation.get_conversation_as_string',
                   return_value='fake convo'):
            orch_convo = OrchestrateConversation(MagicMock())
            context = {"conversation_id": "some_value"}
            cust_prof = {"some_key": "some_value"}
            df = pd.read_csv("eval/tests/data/dummy_scenario.csv")
            copilot_principles_data = {
                "column1": ["value1", "value2"],
                "column2": ["value3", "value4"]
            }
            copilot_principles_df = pd.DataFrame(copilot_principles_data)
            orch_convo.copilot_principles = copilot_principles_df
            data = orch_convo.generate_scenario_convo_dict_helper(df, context, cust_prof)
            assert data[0][CONVO_HISTORY_VAR] == "fake convo"
            # Make sure copilot data got appended
            assert len(data) == 5

            for item in data[-len(copilot_principles_df):]:  # Last items should be from copilot principles
                assert item[SCENARIO_ID_VAR] == df[SCENARIO_ID_VAR].iloc[0]
                assert item[SCENARIO_DESC_VAR] == df[SCENARIO_DESC_VAR].iloc[0]
                assert item[CONVO_ID_VAR] == context["conversation_id"]
                assert item[CONVO_HISTORY_VAR] == "fake convo"
                assert item["customer_profile"] == cust_prof
                assert "exit_due_to_error" in item
                assert "convo_gen_retry" in item

    def test_log_artifact(self):
        """test log_artifact function"""
        gen_convo = "fake_convo"
        completion_tokens = 10
        prompt_tokens = 40
        avg_convo_completion_tokens = 10
        avg_convo_prompt_tokens = 40
        runtime_dict = {'total_runtime': 100}
        fake_artifacts = {
            'generated_convo': 'fake_convo',
            'completion_tokens': completion_tokens,
            'prompt_tokens': prompt_tokens,
            'avg_convo_completion_tokens': avg_convo_completion_tokens,
            'avg_convo_prompt_tokens': avg_convo_prompt_tokens
        }

        with patch(
            "eval.end_to_end.generate_conversation.mlflow"
        ) as fake_mlflow, patch(
            "eval.end_to_end.generate_conversation.open"
        ) as fake_open, patch(
            "eval.end_to_end.generate_conversation.json"
        ):
            fake_cg = MagicMock()
            orch_convo = OrchestrateConversation(fake_cg)
            orch_convo.runtime_dict = runtime_dict
            orch_convo.log_artifacts(fake_artifacts)
            assert fake_mlflow.log_metric.called_with(
                "convo_completion_tokens", completion_tokens
            )
            assert fake_mlflow.log_metric.called_with(
                "convo_prompt_tokens", prompt_tokens
            )
            assert fake_mlflow.log_metric.called_with(
                "avg_convo_convo_completion_tokens", avg_convo_completion_tokens
            )
            assert fake_mlflow.log_metric.called_with(
                "avg_convo_prompt_tokens", avg_convo_prompt_tokens
            )
            assert fake_mlflow.log_dict.called_with(
                gen_convo, artifact_file=CONVO_DATA_FILE_NAME
            )
            assert fake_mlflow.log_dict.called_with(
                runtime_dict, artifact_file=CONVO_RUNTIME_FILE_NAME
            )
            assert fake_open.called

    def test_generate_convo(self):
        """test generate_conversation function"""
        fake_cg = MagicMock()

        orch_convo = OrchestrateConversation(fake_cg)
        orch_convo.generate_structured_convo_data_list = MagicMock()
        orch_convo.log_artifacts = MagicMock()
        fake_gen_convo = {"some_key": "some_value"}
        orch_convo.structured_convo_data_list = fake_gen_convo  # type: ignore
        conv = orch_convo.generate_conversation()
        assert conv == fake_gen_convo
        assert orch_convo.log_artifacts.called
