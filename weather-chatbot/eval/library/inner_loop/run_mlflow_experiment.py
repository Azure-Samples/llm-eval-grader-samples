import os
import glob
import mlflow
from datetime import datetime
import json
import numpy as np
import time

from eval.library.inner_loop.component_base_class import ComponentWrapper

from eval.library.utils.aml_utils import (
    associate_model_w_data,
    is_running_in_aml
)
from eval.library.utils.inner_loop_helpers import load_json_file

from eval.end_to_end.constants import (
    INNER_LOOP_DATA_FOLDER,
    CRITERIA_PROMPT_VAR,
    CONVO_HISTORY_VAR,
    LLM_GRADER_EXPLANATION,
    EXACT_MATCH_RAW
)


def run_mlflow_experiment(
        component: ComponentWrapper,
        test_data_path: list[str],
        output_folder: str) -> None:
    """Run experiment with variants in mlflow and evaluate the output"""

    all_test_data = []
    for path in test_data_path:
        if os.path.isfile(path):
            name_data = os.path.basename(os.path.dirname(os.path.realpath(path)))
            if name_data == INNER_LOOP_DATA_FOLDER:
                name_data = os.path.basename(path)
            all_test_data.extend([load_json_file(path, name_data)])

        elif os.path.isdir(path):
            name_data = os.path.basename(path)
            for filename in glob.glob(f'{path}/**/*.json', recursive=True):
                all_test_data.extend([load_json_file(filename, name_data)])

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    artifact_path = component.__class__.__name__
    exp_name = f'{artifact_path}'
    run_name = f'{artifact_path}_run_{timestamp}'

    # Create experiment
    experiment_id = mlflow.create_experiment(exp_name)

    # Run experiment
    experiment_dct = {}
    experiment_dct["experiment_name"] = exp_name
    experiment_dct["run_name"] = run_name
    experiment_dct['experiment_id'] = experiment_id

    with mlflow.start_run(run_name=run_name, experiment_id=experiment_id) as run:
        # Load mlflow model
        mlflow_model = mlflow.pyfunc.log_model(artifact_path=artifact_path, python_model=component, signature=False)
        loaded_model = mlflow.pyfunc.load_model(model_uri=mlflow_model.model_uri)

        experiment_dct['parent_run_id'] = run.info.run_id

        # Get responses and scores for each test case
        raw_results = []
        all_test_cases = []
        report_card = {}

        start_time = time.time()

        for test_data in all_test_data:
            for test_case in test_data:
                print(f'Test case {test_case["test_case_id"]}')
                # Get response from AICO
                result = loaded_model.predict(test_case)

                # Record result
                test_case['component_output'] = result

                # Score result based on expected_output
                expected_output = test_case['expected_output']
                if test_case.get(CRITERIA_PROMPT_VAR):
                    message_history = test_case['context'][CONVO_HISTORY_VAR]
                    message_history.append({
                        'role': 'assistant',
                        'content': result
                    })
                    parameters = {'component_input': test_case}
                    score = component.measure(parameters=parameters)
                else:
                    parameters = {'expected_output': expected_output, 'result': result}
                    score = component.measure(parameters=parameters)
                test_case['scores'] = score
                for metric in score.keys():
                    if metric not in [LLM_GRADER_EXPLANATION, EXACT_MATCH_RAW]:
                        if metric not in report_card.keys():
                            report_card[metric] = []
                        report_card[metric].append(score[metric])
                all_test_cases.append(test_case)
                raw_results.append(result)

        end_time = time.time()

        # Measure the output and log average of each metric
        avg_score = {}
        for metric, vals_list in report_card.items():
            avg_score[metric] = np.mean(np.array(vals_list))
            mlflow.log_metric(f'avg_{metric}', avg_score[metric])
        overall_score = np.mean(np.array([avg_score[metric] for metric in report_card.keys()]))

        # Build json with test results
        output_json_data = {
            'test_case_data': all_test_cases,
            'avg_scores': avg_score,
            'overall_score': overall_score,
            'seed_prompts': component.seed_prompt(),
        }
        all_scores = [{'test_case_id': test_case['test_case_id'], 'scores': test_case['scores'],
                       'source': test_case['source']} for test_case in output_json_data['test_case_data']]

        # Calculate scores for each file or subdirectory etc.,
        results = []
        sources = set([test["source"] for test in all_scores])
        for source in sources:
            pass_count = 0
            partial_pass_count = 0
            total_count = 0
            for test in all_scores:
                if test["source"] == source:
                    total_count += 1
                    if test["scores"]["exact_match"] == 1:
                        pass_count += 1
                    if test["scores"]["exact_match"] > 0 and test["scores"]["exact_match"] < 1:
                        partial_pass_count += 1

            perc_passed = round((pass_count / total_count) * 100)
            perc_partial_passed = round((partial_pass_count / total_count) * 100)
            results.append({
                "source": source,
                "test_case_passed": f"{pass_count}/{total_count}",
                "test_case_partial_passed": f"{partial_pass_count}/{total_count}",
                "pass_perc": f"{perc_passed}%",
                "partial_pass_perc": f"{perc_partial_passed}%"
            })
        
        overall_pass = sum([test["scores"]["exact_match"] == 1 for test in all_scores])
        overall_partial_pass = sum([1 for test in all_scores if
                                    ((test["scores"]["exact_match"] > 0) and (test["scores"]["exact_match"] < 1))])
        overall_total = len(all_scores)
        overall_total_time = end_time - start_time
        if overall_total > 0:
            overall_perc = round((overall_pass / overall_total) * 100)
            overall_partial_pass_perc = round((overall_partial_pass / overall_total) * 100)
        else:
            overall_perc = 0
            overall_partial_pass_perc = 0
        results.append({
            "overall_pass_results": f"{overall_pass}/{overall_total}",
            "overall_partial_pass_results": f"{overall_partial_pass}/{overall_total}",
            "overall_perc": f"{overall_perc}%",
            "overall_partial_pass_perc": f"{overall_partial_pass_perc}%",
            "overall_total_time": overall_total_time
        })

        results_str = json.dumps(results)

        # Upload data
        file_name = 'data_w_output'
        azure_folder_name = f'{file_name}_{artifact_path}'
        print('run_id', run.info.run_id)
        print('artifact_path', artifact_path)
        mv = mlflow.register_model(f"runs:/{run.info.run_id}/{artifact_path}", artifact_path,
                                   tags={'avg_grade': f'{overall_score}', 'dataset_name': f'{azure_folder_name}',
                                         'run_results': f'{results_str}'})
        model_version = mv.version
        model_name = mv.name

        dataset_desc = f"""This dataset was uploaded automatically for \
            {artifact_path}, version: {model_version} at {timestamp}"""

        # Construct the output JSON folder path from the common prefix
        output_json_folder = os.path.join(output_folder, 'test-results')

        os.makedirs(output_json_folder, exist_ok=True)
        output_json_filename = f'{model_name}_v{model_version}.json'
        output_json_path = os.path.join(output_json_folder, output_json_filename)

        with open(output_json_path, 'w') as f:
            json.dump(output_json_data, f, indent=4)

        # Do not register the dataset when running in AML. The AML
        # pipeline will do this for us
        if not is_running_in_aml():
            # Upload test results to AML, attach to model
            # Pattern matching needed to avoid uploading entire test-results folder.
            pattern = f'*{output_json_filename}'
            print('model_name', model_name)
            print('model_v', model_version)
            associate_model_w_data(
                model_name=model_name,
                model_version=model_version,
                dataset_name=azure_folder_name,
                local_data_path=output_json_folder,
                azure_data_path=azure_folder_name,
                dataset_description=dataset_desc,
                pattern=pattern)
    
        # Print results to terminal
        for result in results:
            print("--------------------------------------")
            if "source" in result:
                print(f"RESULTS FOR {result['source'].upper()}")
                print("--------------------------------------")
                print(f"{result['source']} - {result['test_case_passed']} test cases passed - {result['pass_perc']}")
                print(f"{result['source']} - {result['test_case_partial_passed']} test cases partial passed - {result['partial_pass_perc']}")  # noqa: E501
            else:
                print("OVERALL RESULTS")
                print("--------------------------------------")
                print(f"OVERALL PASS - {result['overall_pass_results']} test cases passed - {result['overall_perc']}")
                print(f"OVERALL PARTIAL PASS - {result['overall_partial_pass_results']} test cases partial passed - {result['overall_partial_pass_perc']}")  # noqa: E501
            print("--------------------------------------")

        print(f"OVERALL EXECUTION TIME - {overall_total_time}")
