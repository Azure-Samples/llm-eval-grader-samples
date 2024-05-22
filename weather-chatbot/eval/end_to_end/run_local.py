import mlflow
from mlflow.exceptions import MlflowException
from datetime import datetime
import os
import shutil
import argparse
import traceback

from eval.end_to_end.evaluate_conversation import EndtoEndEval
from eval.end_to_end.generate_conversation import OrchestrateConversation
from eval.library.conversation_generator.conversation import ConversationGenerator

from eval.library.utils.aml_utils import (
    associate_model_w_data,
    get_run,
    connect_to_aml,
    print_experiment_details,
)
from eval.end_to_end.constants import (
    LOCAL_SCENARIO_DATAPATH,
    LOCAL_END_TO_END_DATAPATH
)
import logging
from dotenv import load_dotenv

load_dotenv()
AML_END_TO_END_DATAPATH = "scenario_data"
END_TO_END_ARTIFACT_PATH = "end_to_end"


def run_mlflow_experiment(output_folder: str):
    """Run mlflow experiment locally and track in aml"""
    # Define required arguments
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    exp_name = f"{END_TO_END_ARTIFACT_PATH}"
    run_name = f"{END_TO_END_ARTIFACT_PATH}_run_{timestamp}"
    MULTI_CRITERIA_GRADING = os.environ["MULTI_CRITERIA_GRADING"].lower() in ("yes", "true", "t", "1")

    print(f'Writing results to {output_folder}')
    # empty and recreate temp dir
    os.makedirs(output_folder, exist_ok=True)

    evaluator = EndtoEndEval(output_folder)

    prompt_dct = {
        "default_system_message": "This is the default system msg"
    }

    # Create experiment if it doesn't exist
    experiment_id = None
    try:
        experiment = mlflow.get_experiment_by_name(exp_name)
        assert experiment is not None
        experiment_id = experiment.experiment_id
    except MlflowException:
        experiment_id = mlflow.create_experiment(exp_name)

    print(f'experiment_id: {experiment_id}')

    # Run experiment
    experiment_dct = {}
    experiment_dct["experiment_id"] = experiment_id
    experiment_dct["experiment_name"] = exp_name
    experiment_dct["run_name"] = run_name

    # Start the mlflow experiment
    with get_run(run_name, experiment_id) as run:
        # log the model, which is code in the end_to_end folder
        mlflow.pyfunc.log_model(
            artifact_path=END_TO_END_ARTIFACT_PATH, python_model=evaluator
        )
        experiment_dct["parent_run_id"] = run.info.run_id
        max_turns = os.environ["CONVO_MAX_TURNS"]
        default_num_convo = os.environ["DEFAULT_NUM_CONVO"]
        cg = ConversationGenerator(max_turns=int(max_turns))
        # Generate and save conversations to evaluate
        convo_orchestrator = OrchestrateConversation(cg, int(default_num_convo))
        json_data = convo_orchestrator.generate_conversation()
        # Evaluate the conversations and save results
        if MULTI_CRITERIA_GRADING:
            aveg_score = evaluator.evaluate_multi_criteria(json_data, prompt_dct)
        else:
            aveg_score = evaluator.evaluate_single_criterion(json_data, prompt_dct)
        # Register the model with the avarege accuracy score
        eval_gpt_model = os.environ["OPENAI_DEPLOYMENT_NAME"]
        assitant_gpt_model = os.environ["OPENAI_DEPLOYMENT_NAME"]
        mv = mlflow.register_model(
            f"runs:/{run.info.run_id}/{exp_name}",
            exp_name,
            tags={"avg_grade": f"{aveg_score}",
                  "eval_gpt_model": f"{eval_gpt_model}",
                  "assitant_gpt_model": f"{assitant_gpt_model}"},
        )
        model_version = mv.version
        model_name = mv.name
        dataset_desc = f"""This dataset was uploaded automatically for {exp_name}, \
            version: {model_version} at {timestamp}"""

        # Do not register the dataset when running in AML. The AML
        # pipeline will do this for us
        print(f'output_folder {output_folder} is != {LOCAL_END_TO_END_DATAPATH} so uploading the dataset')
        # Register data asset in workspace
        data_filepath = LOCAL_SCENARIO_DATAPATH
        data_folderpath = os.path.dirname(data_filepath)
        associate_model_w_data(
            model_name=model_name,
            model_version=model_version,
            dataset_name=AML_END_TO_END_DATAPATH,
            local_data_path=data_folderpath,
            azure_data_path=AML_END_TO_END_DATAPATH,
            dataset_description=dataset_desc)

        return experiment_dct


def run(output_folder: str):
    """Run end to end evaluation on saved dataset"""


    # Run ml flow experiment
    mlflow_tracking_uri = connect_to_aml()
    print("tracking uri: ", mlflow_tracking_uri)
    print("[ Outer Loop Started ]")

    exp = run_mlflow_experiment(output_folder)
    print_experiment_details(exp)
    
    print("[ Outer Loop Ended ]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_folder", type=str, required=False, default=LOCAL_END_TO_END_DATAPATH)
    args, _ = parser.parse_known_args()

    output_folder = args.output_folder

    # Global exception handler -- catch exceptions raised anywhere for easier debugging
    try:
        run(output_folder)
        print('...Assessment complete...')
    except Exception as e:
        print(f'Exception occurred: {e}')
        print(traceback.format_exc())
        raise
