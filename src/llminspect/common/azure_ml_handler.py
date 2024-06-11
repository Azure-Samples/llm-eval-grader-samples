from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    Environment,
    BatchEndpoint,
    CronTrigger,
    JobSchedule,
    PipelineComponentBatchDeployment,
    PipelineJob,
)
from azure.core.exceptions import ResourceNotFoundError

from llmevalgrader.common.logger import get_logger

# get module name
logger = get_logger("azure_ml_handler")


class AzureMLHandler:
    """Class to handle Azure Machine Learning related operations."""

    def __init__(self, subscription_id, resource_group_name, workspace_name):
        self.ml_client = self._initialize_aml_client(
            subscription_id, resource_group_name, workspace_name
        )

    def _initialize_aml_client(
        self,
        subscription_id: str,
        resource_group_name: str,
        workspace_name: str,
    ):
        """Create an MLClient object using the available credentials.

        Args:
            subscription_id (str): Subscription ID
            resource_group_name (str): Resource group name
            workspace_name (str): AML workspace name

        Returns:
            _type_: MLClient
        """
        try:
            credential = DefaultAzureCredential()
            client = MLClient(
                credential,
                subscription_id=subscription_id,
                resource_group_name=resource_group_name,
                workspace_name=workspace_name,
            )

            if client is None:
                logger.exception(f"Unable to create Azure Machine Learning client")
                raise
            logger.info(
                f"Connected to Azure Machine Learning workspace {workspace_name}"
            )
            return client
        except Exception as ex:
            logger.exception(f"Error creating Azure Machine Learning client: {ex}")
            raise

    def get_compute(self, cluster_name: str):
        """Get AML Compute object.

        Args:
            cluster_name (str): cluster name

        Returns:
            _type_: Compute
        """
        compute = None
        error_msg = None
        try:
            compute = self.ml_client.compute.get(cluster_name)
            if compute.type == "amlcompute":
                if compute.provisioning_state != "Succeeded":
                    error_msg = f"Compute cluster {cluster_name} is not in a ready state. Please check and retry."
            elif compute.type == "computeinstance":
                if compute.state != "Running":
                    error_msg = f"Compute instance {cluster_name} not running. Please check and retry."
            if error_msg:
                raise Exception(error_msg)
            logger.info(f"Found compute {cluster_name} in ready state")
            return compute
        except ResourceNotFoundError:
            logger.exception(f"Compute {cluster_name} is not found! ")
            raise
        except Exception as e:
            logger.exception(f"Unable to retrieve compute {cluster_name}: {e}")
            raise

    def get_environment(
        self,
        environment_name: str,
        environment_desc: str,
        environment_base_image_name: str,
        conda_file_path: str,
    ):
        """Get AML environment.

        Args:
            environment_name (str): Name of AML environment
            environment_desc (str): Description of AML environment
            environment_base_image_name (str): Docker image name on top of which conda environment is built
            conda_file_path (str): Conda file path

        Returns:
            _type_: Environment
        """
        try:
            environment = self.ml_client.environments.get(
                environment_name, label="latest"
            )
            logger.info(f"Found environment {environment_name}")
        except ResourceNotFoundError:
            logger.info(
                f"Environment {environment_name} is not found! Creating environment {environment_name}..."
            )
        except Exception:
            logger.exception(f"Unable to access environment {environment_name}")
            raise

        try:
            env_docker_conda = Environment(
                image=environment_base_image_name,
                conda_file=conda_file_path,
                name=environment_name,
                description=environment_desc,
            )
            environment = self.ml_client.environments.create_or_update(env_docker_conda)
            logger.info(f"Environment {environment_name} has been created/updated.")
            return environment
        except Exception:
            logger.exception(f"Unable to create/update environment {environment_name}")
            raise

    def _create_batch_endpoint(self, endpoint_name: str):
        """Create a batch endpoint for the pipeline.

        Args:
            endpoint_name (str): Name of batch endpoint

        Returns:
            endpoint(BatchEndpoint): The created batch endpoint object
        """
        endpoint = BatchEndpoint(
            name=endpoint_name,
        )
        logger.info(f"Creating/updating batch endpoint {endpoint_name}...")
        try:
            batch_endpoint = self.ml_client.batch_endpoints.begin_create_or_update(
                endpoint
            ).result()
            logger.info(
                f"Batch endpoint created/updated successfully with URI: {batch_endpoint.scoring_uri}"
            )
        except Exception as ex:
            logger.exception(f"Error creating batch endpoint: {endpoint.name}")
            raise
        return batch_endpoint

    def publish_pipeline(
        self, endpoint_name: str, pipeline_definition, compute_name: str
    ):
        """
        Publishes the input pipeline to a batch endpoint.

        Args:
            endpoint_name (str): Name of the batch endpoint.
            pipeline_definition: The pipeline to be published.
            compute_name (str): Name of the compute to be used as default for the batch endpoint.
        """

        # Create batch endpoint
        batch_endpoint = self._create_batch_endpoint(endpoint_name)

        # Transform pipeline into a component
        pipeline_component = self.ml_client.components.create_or_update(
            pipeline_definition().component
        )

        # Configure batch deployment
        batch_deployment = PipelineComponentBatchDeployment(
            name=f"{endpoint_name}",
            endpoint_name=batch_endpoint.name,
            component=pipeline_component,
            settings={
                "continue_on_step_failure": False,
                "default_compute": compute_name,
            },
        )

        # Create batch deployment
        self.ml_client.batch_deployments.begin_create_or_update(
            batch_deployment
        ).result()

        logger.info(
            f"Pipeline published successfully to batch endpoint {batch_endpoint.name} under deployment {batch_deployment.name}"
        )

        # Configure new batch deployment as default for batch endpoint
        batch_endpoint.defaults.deployment_name = batch_deployment.name
        self.ml_client.batch_endpoints.begin_create_or_update(batch_endpoint).result()

    def schedule_pipeline(self, pipeline_job, schedule_name: str, schedule: str, schedule_start_time: str):
        """Schedule the pipeline."""
        if schedule_start_time is None or not schedule_start_time.strip():
            # set schedule start time to tomorrow
            schedule_start_time = datetime.combine((datetime.now() + timedelta(days=1)).date(), datetime.min.time())
        cron_trigger = CronTrigger(
            expression=schedule,
            start_time=schedule_start_time
        )

        job_schedule = JobSchedule(
            name=schedule_name, trigger=cron_trigger, create_job=pipeline_job
        )

        job_schedule = self.ml_client.schedules.begin_create_or_update(schedule=job_schedule).result()
        logger.info(f"Pipeline {job_schedule.create_job.display_name} scheduled successfully to run starting {job_schedule.trigger.start_time}")
    
    def submit_pipeline_job(self, pipeline_job: PipelineJob, experiment_name: str):
        """Submit an AML pipeline job.
        Args:
            pipeline_job (Job): Azure Machine Learning pipeline job
            experiment_name (str): Name of the experiment
        Returns:
            PipelineJob: The submitted pipeline job object
        """
        try:
            submitted_job = self.ml_client.jobs.create_or_update(
                pipeline_job, experiment_name=experiment_name
            )
            logger.info(f"Pipeline job submitted for experiment: {experiment_name}")
            return submitted_job
        except Exception as ex:
            logger.exception(f"Error submitting pipeline job: {ex}")
            raise
