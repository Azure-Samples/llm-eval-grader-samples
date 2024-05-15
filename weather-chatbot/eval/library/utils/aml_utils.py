from typing import Dict
from azureml.core.model import Model
from azureml.core import Workspace, Datastore, Dataset, Experiment
from azureml.core.run import Run
from azureml.data.datapath import DataPath
from dotenv import load_dotenv
import os
import logging
import traceback

import mlflow


DATASTORE_NAME = "workspaceblobstore"

load_dotenv()

logging.basicConfig(level=logging.ERROR)


def get_workspace() -> Workspace:
    """Create aml workspace."""

    return Workspace.get(
        name=os.environ.get("AML_WORKSPACE_NAME"),
        subscription_id=os.environ.get("AML_SUBSCRIPTION_ID"),
        resource_group=os.environ.get("AML_RESOURCE_GROUP"),
    )


def get_azure_model(ws, model_name: str, version: int) -> Model:
    """Connect to AML workspace.

    Args:
        ws (_type_): Azure Workspace
        model_name (str): Model Name
        version (int): Model version

    Returns:
        _type_: Connected AML workspace instance
    """
    model = Model(ws, model_name, version=version)

    return model


def get_dataset(ws, azure_data_path) -> Dataset:
    """Get dataset from aml datastore.

    Args:
        ws (_type_): Azure workspace
        local_data_path (str): Relative local path of file to upload
        azure_data_path (str): Directory name where file gets uploaded
    """
    datastore = Datastore.get(ws, DATASTORE_NAME)

    dataset = Dataset.File.from_files(path=(datastore, azure_data_path))
    return dataset


def get_run(run_name: str, experiment_id: str) -> mlflow.ActiveRun:
    """Return the active mlflow run or start one if it doesn't exist
    (when running locally)

    Args:
        run_name (str): The run name to assign if we need to create the run
        experiment_id (str): The experiment_id to assign if we need to create the run
    """
    run = mlflow.active_run()

    if run is None:
        run = mlflow.start_run(run_name=run_name, experiment_id=experiment_id)

    return run


def connect_to_aml() -> str:
    """Get MLFlow tracking URI."""
    ws = get_workspace()
    mlflow_tracking_uri = ws.get_mlflow_tracking_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    return mlflow_tracking_uri


def create_dataset(ws, local_data_path: str, azure_data_path: str, pattern=None) -> None:
    """Create a dataset from the specified path.

    Args:
        ws (_type_): Azure workspace
        local_data_path (str): Relative local path of file to upload
        azure_data_path (str): Directory name where file gets uploaded
    """
    datastore = Datastore.get(ws, DATASTORE_NAME)

    print(f'Uploading src_dir {local_data_path} to {datastore} / {azure_data_path}')
    Dataset.File.upload_directory(
        src_dir=local_data_path,
        target=DataPath(datastore, azure_data_path),
        show_progress=True,
        overwrite=True,
        pattern=pattern
    )
    print(f'Upload complete')


def associate_model_w_data(
    model_name: str,
    model_version: int,
    dataset_name: str,
    local_data_path: str,
    azure_data_path: str,
    dataset_description: str,
    pattern=None
) -> None:
    """Associate the model with the specified data.

    Args:
        model_name (str): Name of the model registered in AML model registry
        model_version (int): Version of model you want to link dataset to
        dataset_name (str): Pick a name for the dataset
        local_data_path (str): Relative local path of file to upload
        azure_data_path (str): Directory name where file gets uploaded
        dataset_description (str): Give a description of your dataset
    """
    try:
        # Get workspace
        ws = get_workspace()

        # Upload dataset to datastore
        create_dataset(
            ws=ws, local_data_path=local_data_path, azure_data_path=azure_data_path, pattern=pattern
        )

        print('Create_dataset complete')
        # Get datastore instance
        datastore = Datastore(workspace=ws, name=DATASTORE_NAME)

        # Read file as a data asset from datastore
        print(f'Reading dataset back from AML: {azure_data_path}')
        json_dataset = Dataset.File.from_files(path=[(datastore, f"{azure_data_path}")])

        # Register data asset in workspace
        reg_data = json_dataset.register(
            workspace=ws, name=dataset_name, description=dataset_description, create_new_version=True
        )

        # Get instance of model given name and version
        model = get_azure_model(ws=ws, model_name=model_name, version=model_version)

        # Link registered data asset to your model instance
        model.add_dataset_references([(dataset_name, reg_data)])
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def view_last_n_runs(model_name: str, metric_name: str, n: int = 5) -> None:
    """Display metrics for the last `n` runs of a registered model.

    Args:
        model_name (str): The name of the registered model to display metrics for.
        metric_name (str): The name of the metric to display.
        n (int): The number of past runs to display. Default is 5.
    """
    # Find the registered models with the given name
    models = mlflow.search_model_versions(
        filter_string=f"name='{model_name}'", max_results=n, order_by=["version DESC"]
    )

    # Get the version and metric value for each of the past `n` runs
    versions_metrics = []
    for model in models:
        tags = model.tags
        version = model.version
        metric_value = None
        if metric_name in tags:
            metric_value = float(tags.get(metric_name))
        versions_metrics.append((version, metric_value))

    # Display the results
    print(f"Model: {model_name}")
    print(f"Metric: {metric_name}")
    print("Version | Metric Value")
    print("-" * 20)
    for version, metric_value in versions_metrics:
        if metric_value is not None:
            print(f"{version}     | {metric_value}")
        else:
            print(f"{version}     | N/A")


def download_model_and_data(model_name: str, version_num: int, directory: str) -> None:
    """Download code and data for a specific version of a registered model.

    Args:
        model_name (str): The name of the registered model.
        version_num (int): The version number of the desired model version.
        directory (str): The directory to download the code to.
    """
    ws = get_workspace()

    # Download the artifacts for the specified model version
    model = Model(workspace=ws, name=model_name, version=version_num)
    print(f"Downloading artifacts for {model_name} version {version_num}...")
    model.download(target_dir=directory, exist_ok=True)

    # Get dataset name from tag
    dataset_name = model.tags.get("dataset_name") or model.properties.get(
        "dataset_name"
    )

    if dataset_name:
        # Get the dataset
        dataset = Dataset.get_by_name(workspace=ws, name=dataset_name)
        # Download the dataset
        print(f"Downloading dataset with name: {dataset_name}")
        dataset.download(target_path=directory, overwrite=True)
    else:
        raise ValueError(
            f"No dataset name found for model {model_name}, version {version_num}"
        )


def print_experiment_details(experiment_dct: Dict) -> None:
    """Retrieve and print details from experiment_dct."""
    experiment_name = experiment_dct["experiment_name"]
    experiment = Experiment(get_workspace(), experiment_name)
    parent_run_id = experiment_dct["parent_run_id"]

    print(f"Run id for current variant is: {parent_run_id}")

    experiment_run = Run(experiment, parent_run_id)
    run_url = experiment_run.get_portal_url()
    parent_run = mlflow.get_run(run_id=parent_run_id)
    artifact_uri = str(parent_run.info.artifact_uri)
    print(f"Run portal URL: {run_url}")
    print(f"URI where artifact is stored is: {artifact_uri}")
    print(f"The metrics recorded for this variant are:{parent_run.data.metrics}")
    print(f"The parameters for this variant are:{parent_run.data.params}")
