# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest import TestCase
from unittest.mock import patch

from eval.end_to_end.run_local import (
    run_mlflow_experiment,
    run,
)


class TestRunLocalObject(TestCase):
    def test_run_mlflow_experiement(self):
        with patch(
            "eval.end_to_end.run_local.EndtoEndEval"
        ) as fake_evaluator, patch(
            "eval.end_to_end.run_local.get_run"
        ), patch(
            "eval.end_to_end.run_local.mlflow"
        ), patch(
            "eval.end_to_end.run_local.mlflow.get_experiment_by_name"
        ) as fake_get_experiment_by_name, patch(
            "eval.end_to_end.run_local.os"
        ), patch(
            "eval.end_to_end.run_local.OrchestrateConversation"
        ) as fake_orchestrator, patch(
            "eval.end_to_end.run_local.shutil"
        ), patch(
            "eval.end_to_end.run_local.ConversationGenerator"
        ) as fake_generator, patch(
            "eval.end_to_end.run_local.associate_model_w_data"
        ):
            run_mlflow_experiment(output_folder='fake_output_folder')

            assert fake_get_experiment_by_name.called_once()
            assert fake_evaluator.called_once()
            assert fake_generator.called_once()
            assert fake_orchestrator.called_once()

    def test_run(self):
        with patch(
            "eval.end_to_end.run_local.connect_to_aml"
        ) as fake_connect, patch(
            "eval.end_to_end.run_local.run_mlflow_experiment"
        ) as fake_run_mlflow, patch(
            "eval.end_to_end.run_local.print_experiment_details"
        ) as fake_print:
            run(output_folder='fake_output_folder')
            assert fake_connect.called_once()
            assert fake_run_mlflow.called_once()
            assert fake_print.called_with(fake_run_mlflow)
