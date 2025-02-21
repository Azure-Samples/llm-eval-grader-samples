# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest import TestCase
from unittest.mock import patch, MagicMock
import pytest
import os
import json

from eval.library.utils.aml_utils import (
    get_workspace,
    get_azure_model,
    get_dataset,
    connect_to_aml,
    create_dataset,
    associate_model_w_data,
    download_model_and_data,
    get_run,
    view_last_n_runs,
    print_experiment_details
)

class TestAmlUtilsObject(TestCase):
    @pytest.fixture(scope='module', autouse=True)
    def setup(self):
        """ Set mock environment variables needed for each test """
        env_path = 'eval/tests/data/dummy_env.json'
        with open(env_path, 'r') as f_p:
            mock_variables = json.load(f_p)

        with patch.dict(os.environ, mock_variables):
            yield

    def test_get_workspace(self):
        with patch("azureml.core.Workspace.get") as mock_workspace:
            get_workspace()
            assert mock_workspace.call_count == 1

    def test_get_azure_model(self):
        fake_ws = "fake"
        model_name = "fake_name"
        version = 0

        with patch(
            "eval.library.utils.aml_utils.Model"
        ) as mock_model:
            model = get_azure_model(fake_ws, model_name, version)
            assert model is not None
            assert mock_model.call_count == 1

    def test_get_dataset(self):
        fake_ws = MagicMock()
        path = "fake_path"

        with patch(
            "eval.library.utils.aml_utils.Datastore"
        ) as mock_datastore, patch(
            "eval.library.utils.aml_utils.Dataset"
        ):
            dataset = get_dataset(fake_ws, path)
            assert dataset is not None
            assert mock_datastore.get.call_count == 1

    def test_connect_aml(self):
        fake_mlflow_tracking_uri = 'foo'
        fake_workspace = MagicMock()
        fake_workspace.get_mlflow_tracking_uri.return_value = fake_mlflow_tracking_uri

        with patch(
            "eval.library.utils.aml_utils.get_workspace"
        ) as mock_get_workspace, patch(
            "eval.library.utils.aml_utils.mlflow"
        ) as mock_mlflow:
            mock_get_workspace.return_value.get_mlflow_tracking_uri.return_value = fake_mlflow_tracking_uri

            actual_mlflow_tracking_uri = connect_to_aml()

            assert actual_mlflow_tracking_uri == fake_mlflow_tracking_uri
            mock_get_workspace.assert_called_once()
            mock_mlflow.set_tracking_uri.assert_called_with(fake_mlflow_tracking_uri)

    def test_create_dataset(self):
        ws = "fake_ws"
        local_data_path = "fake_path"
        azure_data_path = "fake_path"
        pattern = 'pattern'
        with patch(
            "eval.library.utils.aml_utils.Datastore"
        ) as mock_dtstore, patch(
            "eval.library.utils.aml_utils.Dataset"
        ) as mock_dtset, patch(
            "eval.library.utils.aml_utils.DataPath"
        ) as mock_dtpath:
            create_dataset(ws, local_data_path, azure_data_path, pattern)
            assert mock_dtstore.get.called_with(ws)
            assert mock_dtset.File.upload_directory.called_with(
                local_data_path, mock_dtpath, pattern
            )
            assert mock_dtpath.called_with(mock_dtstore, azure_data_path)

    def test_associate_model_w_data(self):
        model_name = "model"
        model_version = 0
        dataset_name = "data_set"
        local_data_path = "path"
        azure_data_path = "path"
        dataset_description = "description"
        pattern = "pattern"

        with patch(
            "eval.library.utils.aml_utils.get_workspace"
        ) as mock_get_workspace, patch(
            "eval.library.utils.aml_utils.create_dataset"
        ) as mock_create_dataset, patch(
            "eval.library.utils.aml_utils.Datastore"
        ) as mock_datastore, patch(
            "eval.library.utils.aml_utils.Dataset"
        ) as mock_dataset, patch(
            "eval.library.utils.aml_utils.get_azure_model"
        ) as mock_get_azure_model:
            associate_model_w_data(
                model_name=model_name,
                model_version=model_version,
                dataset_name=dataset_name,
                local_data_path=local_data_path,
                azure_data_path=azure_data_path,
                dataset_description=dataset_description,
                pattern=pattern
            )
            mock_get_workspace.assert_called()
            mock_create_dataset.assert_called_with(
                ws=mock_get_workspace(), local_data_path=local_data_path, azure_data_path=azure_data_path,
                pattern=pattern
            )
            assert mock_datastore.get.called_with(mock_get_workspace)
            assert mock_dataset.File.from_files.called_once()
            assert mock_get_azure_model.called_with(
                mock_get_workspace, model_name, model_version
            )

    def test_download_model_and_data(self):
        model_name = "model"
        directory = "directory"
        version_num = 0

        with patch(
            "eval.library.utils.aml_utils.get_workspace"
        ) as mock_get_workspace, patch(
            "eval.library.utils.aml_utils.Model"
        ) as mock_Model, patch(
            "eval.library.utils.aml_utils.Datastore"
        ) as mock_datastore, patch(
            "eval.library.utils.aml_utils.Dataset"
        ) as mock_dataset:
            download_model_and_data(model_name, version_num, directory)
            assert mock_get_workspace.called_once()
            assert mock_Model.called_with(model_name, version_num)
            assert mock_datastore.called_once()
            assert mock_dataset.caled_once()

    def test_get_run(self):

        fake_run_name = 'foo'
        fake_experiment_id = 'bar'
        fake_run = {'i am a fake run object'}

        with patch(
                "eval.library.utils.aml_utils.mlflow.active_run"
        ) as mock_mlflow_active_run, patch(
                "eval.library.utils.aml_utils.mlflow.start_run") as mock_mlflow_start_run:

            mock_mlflow_active_run.return_value = None
            mock_mlflow_start_run.return_value = fake_run

            run = get_run(fake_run_name, fake_experiment_id)
            assert mock_mlflow_active_run.caled_once()
            assert mock_mlflow_start_run.called_with(fake_run_name, fake_experiment_id)
            assert run == fake_run

    def test_view_last_n_runs(self):
        fake_model_name = 'fake_model'
        fake_metric_name = 'fake_metric'
        n = 2

        printed_header_line_count = 4

        fake_models = []
        for i in range(0, n):
            new_model = MagicMock()

            # Ensure that we hit paths for metric_value being assigned
            # and unassigned by populating new_model.tags for even entries
            if i % 2 == 0:
                new_model.tags = {fake_metric_name: i}
            new_model.version = i
            fake_models.append(new_model)

        with patch(
            "eval.library.utils.aml_utils.mlflow"
        ) as mock_mlflow, patch(
            "eval.library.utils.aml_utils.print"
        ) as mock_print:
            mock_mlflow.search_model_versions.return_value = fake_models

            view_last_n_runs(fake_model_name, fake_metric_name, n)

            mock_mlflow.search_model_versions.assert_called_once()
            assert mock_print.call_count == printed_header_line_count + n

    def test_print_experiment_details(self):
        fake_experiment_name = "fake_experiment_name",
        fake_workspace_name = "fake_workspace"
        fake_portal_url = "fake portal_url"
        fake_config_json = "fake_config_json"
        fake_artifact_uri = "fake_artifact_uri"
        fake_metrics = "fake_metrics"
        fake_params = "fake_params"
        fake_parent_run_id = "fake_parent_run_id"

        fake_experiment_dct = {
            "experiment_name": fake_experiment_name,
            "parent_run_id": fake_parent_run_id
        }

        expected_printed_strings = [
            fake_parent_run_id,
            fake_portal_url,
            fake_artifact_uri,
            fake_config_json,
            fake_metrics,
            fake_params,
        ]

        with patch(
            "eval.library.utils.aml_utils.Experiment"
        ) as mock_experiment, patch(
            "eval.library.utils.aml_utils.get_workspace"
        ) as mock_get_workspace, patch(
            "eval.library.utils.aml_utils.Run"
        ) as mock_run, patch(
            "eval.library.utils.aml_utils.mlflow"
        ) as mock_mlflow, patch(
            "eval.library.utils.aml_utils.print"
        ) as mock_print:
            mock_get_workspace.return_value = fake_workspace_name
            mock_run.return_value.get_portal_url.return_value = fake_portal_url
            mock_mlflow.get_run.return_value.info.artifact_uri = fake_artifact_uri
            mock_mlflow.get_run.return_value.data.metrics = fake_metrics
            mock_mlflow.get_run.return_value.data.params = fake_params
            mock_mlflow.artifacts.load_dict.return_value = fake_config_json

            print_experiment_details(fake_experiment_dct)

            assert mock_print.call_count == 5

            # Verify that the expected strings were printed
            for expected_string in expected_printed_strings:
                matches = [call for call in mock_print.call_args_list if expected_string in call.args[0]]
                assert matches is not None

            mock_experiment.assert_called_once_with(fake_workspace_name, fake_experiment_name)
            mock_get_workspace.assert_called_once()
            mock_run.return_value.get_portal_url.assert_called_once()
