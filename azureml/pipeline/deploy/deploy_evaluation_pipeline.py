import json
import os
import subprocess
import yaml
from dotenv import load_dotenv
from azure.ai.ml import Input, Output, load_component
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.dsl import pipeline

from llmevalgrader.common.azure_ml_handler import AzureMLHandler
from llmevalgrader.common.config_handler import get_evaluator_info
from llmevalgrader.common.entities import App, Evaluator

from llmevalgrader.common.logger import get_logger

logger = get_logger("deploy_evaluation_pipeline")

pipeline_components = []

def create_dynamic_evaluation_pipeline(
        app_info,
        evaluator_name,
        metric_names,        
        fact_evaluation_input,
        prepped_evaluation_data_path,
        pf_output_data_path,
        key_vault_url,
        pipeline_name
    ):
    """
        Construct evaluation pipeline definition dynamically for a specific app and evaluator.

        Args:
            app_info (str): Info of the application.
            evaluator_name (str): Name of the evaluator.
            metric_names (list(dict)): List of dictionaries containing name, version and allowed values of the metrics generated from the evaluation.
            fact_evaluation_input (Input): Input object representing fact evaluation data.
            prepped_evaluation_data_path (Output): Output object representing prepped evaluation data.
            pf_output_data_path (Output): Output object representing promptflow output data.
            key_vault_url (str): URL of the key vault.
            pipeline_name (str): Name of the pipeline.
    """
    @pipeline(
        name=pipeline_name,
        display_name=pipeline_name,
        experiment_name=app_info.app_name
    )
    def evaluation_pipeline(
            evaluation_data_start_date: str,
            evaluation_data_end_date: str
        ):
        prepped_evaluation_data = Output(path=prepped_evaluation_data_path, type=AssetTypes.URI_FOLDER, mode="rw_mount")

        prep_data = pipeline_components[0](
            app_name=app_info.app_name,
            app_type=app_info.app_type,
            evaluator_name=evaluator_name,
            metric_names=metric_names,
            start_date=evaluation_data_start_date,
            end_date=evaluation_data_end_date,
            gold_zone_eval_fact_path=fact_evaluation_input,
            key_vault_url=key_vault_url
            )
        prep_data.outputs.prep_data_output_path = prepped_evaluation_data

        pf_output = Output(path=pf_output_data_path, type=AssetTypes.URI_FOLDER, mode="rw_mount")

        evaluation = pipeline_components[1](
            data=prep_data.outputs.prep_data_output_path,
            evaluation_dataset="${data.evaluation_dataset}",
            )
        evaluation.outputs.flow_outputs = pf_output

        write_metrics = pipeline_components[2](
            eval_dataset_path=prep_data.outputs.prep_data_output_path,
            eval_metrics_data_path=evaluation.outputs.flow_outputs,
            key_vault_url=key_vault_url
            )

    return evaluation_pipeline

def build_pipeline(
        app_info: App,
        evaluator_info: Evaluator,
        aml_key_vault_url: str,
        aml_datastore_gold_zone_path: str,
        aml_datastore_evaluation_path: str,
        pipeline_name: str
    ):
    """
    Constructs an Azure Machine Learning pipeline. It encapsulates the process of defining pipeline inputs,
    loading pipeline components from YAMLs, configuring component environments settings, configuring pipeline settings etc.

    Args:
        app_info (App): Information about the application for which evaluation is run.
        evaluator_info (Evaluator): Information about the evaluator used.
        aml_compute_name (str): Name of the AML compute.
        aml_key_vault_url (str): URL of the Azure Key Vault.
        aml_datastore_gold_zone_path (str): AML datastore path for gold zone input data.
        aml_datastore_evaluation_path (str): AML datastore path for evaluation output data.
        pipeline_name (str): Name of the pipeline.

    Returns:
        PipelineJob: Azure Machine Learning pipeline job.
    """
    
    fact_evaluation_dataset_folder = "fact_evaluation_dataset/fact_evaluation_dataset/"
    fact_evaluation_input = Input(path=aml_datastore_gold_zone_path + fact_evaluation_dataset_folder, type=AssetTypes.URI_FOLDER)

    app_path = app_info.app_name + "/" + evaluator_info.evaluator_name
    prepped_evaluation_data_path = aml_datastore_evaluation_path + "in-prepped-data/" + app_path.replace("_", "-") + "/${{name}}/"
    pf_output_data_path = aml_datastore_evaluation_path + "out-evaluation-metrics/" + app_path.replace("_", "-") + "/${{name}}/"

    prep_data_component = load_component("../components/definition/prep_data.yml")
    evaluation_promptflow_component = load_component(evaluator_info.evaluation_flow_path)
    write_metrics_component = load_component("../components/definition/write_metrics.yml")

    pipeline_components.append(prep_data_component)
    pipeline_components.append(evaluation_promptflow_component)
    pipeline_components.append(write_metrics_component)

    metric_names = [
        {"metric_name": metric.metric_name, "metric_version": evaluator_info.evaluation_metrics_version, "metric_allowed_values": metric.metric_allowed_values}
        for metric in evaluator_info.evaluation_metrics
    ]

    pipeline_definition = create_dynamic_evaluation_pipeline(
        app_info=app_info,
        evaluator_name=evaluator_info.evaluator_name,
        metric_names=json.dumps(metric_names).replace('"', '\\"'),
        fact_evaluation_input=fact_evaluation_input,
        prepped_evaluation_data_path=prepped_evaluation_data_path,
        pf_output_data_path=pf_output_data_path,
        key_vault_url=aml_key_vault_url,
        pipeline_name=pipeline_name
    )

    return pipeline_definition
  
def validate_promptflow(promptflow_path: str):
    """
    Validates the evaluation prompt flow and generates a flow.tools.json under .promptflow folder.

    Args:
        promptflow_path (str): Path to the evaluation prompt flow source code.
    """
    try:
        logger.info(f"Validating prompt flow {promptflow_path}...")
        subprocess.run(["pf", "flow", "validate", "--source", promptflow_path], capture_output=True, check=True)
        logger.info(f"Prompt flow validation successful for {promptflow_path}")
    except subprocess.CalledProcessError as ex:
        logger.exception(f"Exception while running prompt flow validate for {promptflow_path}: {ex.stderr.decode('utf-8')}")
        raise

def main():
    """Build and publish evaluation pipelines"""
    load_dotenv()
    subscription_id = os.getenv("SUBSCRIPTION_ID")
    resource_group_name = os.getenv("RESOURCE_GROUP_NAME")
    workspace_name = os.getenv("AML_WORKSPACE_NAME")
    key_vault_url = os.getenv("KEY_VAULT_URL")

    aml_config_file_path = "../config/aml_config.yml"
    evaluation_config_file_path = "../config/evaluation_config.yml"

    with open(aml_config_file_path, 'r') as file:
        aml_config = yaml.safe_load(file)

    compute_name = aml_config["compute"]["name"]
    aml_datastore_gold_zone_path = aml_config["datastore"]["gold_zone"]
    aml_datastore_evaluation_path = aml_config["datastore"]["evaluation"]    

    # Initialize Azure Machine Learning handler
    aml_handler = AzureMLHandler(subscription_id, resource_group_name, workspace_name)
    
    # Check if AML compute exists
    compute = aml_handler.get_compute(compute_name)

    evaluators = get_evaluator_info(evaluation_config_file_path)        

    for evaluator in evaluators:
        # Validate promptflow
        validate_promptflow(evaluator.evaluation_flow_path)


        evaluation_name = f"{evaluator.evaluator_name}-evaluation-{evaluator.app.app_name}".replace("_", "-")
        experiment_name = evaluator.app.app_name

        # Build pipeline definition
        logger.info(f"Building pipeline for {evaluation_name}...")
        pipeline_definition = build_pipeline(
            app_info=evaluator.app,
            evaluator_info=evaluator,
            aml_key_vault_url=key_vault_url,
            aml_datastore_gold_zone_path=aml_datastore_gold_zone_path,
            aml_datastore_evaluation_path=aml_datastore_evaluation_path,
            pipeline_name=evaluation_name.replace("-", "_")
        )

        # Publish pipeline to batch endpoint
        logger.info(f"Publishing pipeline for {evaluation_name}...")
        aml_handler.publish_pipeline(
            endpoint_name=evaluator.evaluation_endpoint,
            pipeline_definition=pipeline_definition,
            compute_name=compute_name
        )

        logger.info(f"Scheduling pipeline for {evaluation_name}...")        
        # When a scheduled pipeline job, we calculate the input dates dynamically within the pipeline components
        pipeline_job = pipeline_definition(
            evaluation_data_start_date="NA",
            evaluation_data_end_date="NA"
        )
        pipeline_job.settings.default_compute = compute_name
        pipeline_job.experiment_name = experiment_name
        
        aml_handler.schedule_pipeline(
            pipeline_job=pipeline_job,
            schedule_name=evaluation_name, # All the display name of jobs triggered by schedule will have the display name as <schedule_name>-YYYYMMDDThhmmssZ
            schedule=evaluator.evaluation_schedule,
            schedule_start_time=evaluator.evaluation_schedule_start_time
        )
        
        pipeline_components.clear()

if __name__ == "__main__":
    main()