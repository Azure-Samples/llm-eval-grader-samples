"""This script is used to deploy the pipeline for data transformation for evaluation dataset."""
import argparse
import os
import yaml
from dotenv import load_dotenv
from azure.ai.ml import Output, Input, load_component
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.dsl import pipeline

from llminspect.common.azure_ml_handler import AzureMLHandler
from llminspect.common.config_handler import get_transformer_info
from llminspect.common.entities import Transformer
from llminspect.transformation.transform  import DataTransformer
from llminspect.common.logger import get_logger


logger = get_logger("deploy_transformation_pipeline")


pipeline_components = []

def create_dynamic_evaluation_pipeline(
        chatbot_name,
        data_source,
        mapping_list,
        fact_evaluation_output_path,
        dim_metadata_output_path,
        dim_conversation_output_path,
        key_vault_url,
        pipeline_name
    ):
  
    @pipeline(
        name=pipeline_name,
        display_name=pipeline_name
    )
    def transformation_pipeline(
        transformation_start_date: str,
        transformation_end_date: str
    ):
        """
        Transformation pipeline definition

        Args:
            transformation_start_date (str): Start date of data against which data transformation is run.
            transformation_end_date (str): End date of data against which data transformation is run.
        """
        transformation_component = pipeline_components[0](
            chatbot_name=chatbot_name,
            data_source=data_source,
            mapping_list=mapping_list,
            start_date=transformation_start_date,
            end_date=transformation_end_date,
            key_vault_url=key_vault_url,
        )

        fact_evaluation_output = Output(path=fact_evaluation_output_path, type=AssetTypes.URI_FOLDER, mode="rw_mount")
        dim_metadata_output = Output(path=dim_metadata_output_path, type=AssetTypes.URI_FOLDER, mode="rw_mount")
        dim_conversation_output = Output(path=dim_conversation_output_path, type=AssetTypes.URI_FOLDER, mode="rw_mount")

        transformation_component.outputs.fact_evaluation_output = fact_evaluation_output
        transformation_component.outputs.dim_metadata_output = dim_metadata_output
        transformation_component.outputs.dim_conversation_output = dim_conversation_output
    
    return transformation_pipeline

def build_pipeline(
        transformer_info: Transformer,
        aml_key_vault_url: str,
        aml_datastore_gold_zone_path: str,
        pipeline_name: str
    ):
    """
    Constructs an Azure Machine Learning pipeline. It encapsulates the process of defining pipeline inputs,
    loading pipeline components from YAMLs, configuring component environments settings, configuring pipeline settings etc.

    Args:
        transformer_info (Transformer): Information about the transformer.
        aml_compute_name (str): Name of the Azure Machine Learning compute.
        aml_key_vault_url (str): URL of the Azure Key Vault.
        aml_datastore_gold_zone_path (str): Path to the gold zone in the Azure Machine Learning datastore.
        transformation_start_date (str): Start date of data against which data transformation is run.
        transformation_end_date (str): End date of data against which data transformation is run.
        pipeline_name (str): Name of the pipeline.

    Returns:
        PipelineJob: Azure Machine Learning pipeline job.
    """
    # Input to the pipeline
    chatbot_name = transformer_info.chatbot_name
    data_source = transformer_info.data_source
    mapping_list = transformer_info.get_mapping_list()

    # Output of the pipeline
    fact_evaluation_dataset_folder = "fact_evaluation_dataset/fact_evaluation_dataset/"
    fact_evaluation_output_path = aml_datastore_gold_zone_path + fact_evaluation_dataset_folder
    dim_metadata_output_path = aml_datastore_gold_zone_path + "dim_metadata/"
    dim_conversation_output_path = aml_datastore_gold_zone_path + "dim_conversation/"

    transformation_component = load_component("../components/definition/transformation.yml")

    pipeline_components.append(transformation_component)

    pipeline_definition = create_dynamic_evaluation_pipeline(
        chatbot_name=chatbot_name,
        data_source=str(data_source.to_dict()),
        mapping_list=str(mapping_list.to_dict()),
        fact_evaluation_output_path=fact_evaluation_output_path,
        dim_metadata_output_path=dim_metadata_output_path,
        dim_conversation_output_path=dim_conversation_output_path,
        key_vault_url=aml_key_vault_url,
        pipeline_name=pipeline_name
    )

    return pipeline_definition

def main():
    """
    Build and publish transformation pipelines.

    This function reads configuration files, builds and publishes transformation pipelines
    based on the information provided in the configuration files. It also schedules the
    pipelines to run at specified intervals.

    Returns:
        None
    """
    load_dotenv()
    subscription_id = os.getenv("SUBSCRIPTION_ID")
    resource_group_name = os.getenv("RESOURCE_GROUP_NAME")
    workspace_name = os.getenv("AML_WORKSPACE_NAME")
    key_vault_url = os.getenv("KEY_VAULT_URL")

    aml_config_file_path = "../config/aml_config.yml"

    transformation_config_file_path = "../config/transformation_config.yml"
    
    with open(aml_config_file_path, 'r') as file:
        aml_config = yaml.safe_load(file)

    compute_name = aml_config["compute"]["name"]
    aml_datastore_gold_zone_path = aml_config["datastore"]["gold_zone"]

    # Initialize Azure Machine Learning handler
    aml_handler = AzureMLHandler(subscription_id, resource_group_name, workspace_name)

    # Check if AML compute exists
    compute = aml_handler.get_compute(compute_name)

    # Get information about transformers from the configuration files
    transformers = get_transformer_info(transformation_config_file_path)
    
    for transformer in transformers:
        transformation_name = f"{transformer.chatbot_name.lower()}-transformation-{transformer.name}"
        experiment_name = transformer.chatbot_name.lower()

        # Build pipeline definition
        logger.info(f"Building pipeline for {transformation_name}...")
        pipeline_definition = build_pipeline(
            transformer_info=transformer,
            aml_key_vault_url=key_vault_url,
            aml_datastore_gold_zone_path=aml_datastore_gold_zone_path,            
            pipeline_name=transformation_name.replace("-", "_")
        )

        # Publish pipeline to batch endpoint
        logger.info(f"Publishing pipeline for {transformation_name}...")
        aml_handler.publish_pipeline(
            endpoint_name=transformer.endpoint,
            pipeline_definition=pipeline_definition,
            compute_name=compute_name
        )

        logger.info(f"Scheduling pipeline for {transformation_name}...")        
        # When a scheduled pipeline job, we calculate the input dates dynamically within the pipeline components
        pipeline_job = pipeline_definition(
            transformation_start_date="NA",
            transformation_end_date="NA"
        )
        pipeline_job.settings.default_compute = compute_name
        pipeline_job.experiment_name = experiment_name
        aml_handler.schedule_pipeline(
            pipeline_job=pipeline_job,
            schedule_name=transformation_name, # All the display name of jobs triggered by schedule will have the display name as <schedule_name>-YYYYMMDDThhmmssZ
            schedule=transformer.schedule,
            schedule_start_time=transformer.schedule_start_time
        )
        
        pipeline_components.clear()

if __name__ == "__main__":
    main()
