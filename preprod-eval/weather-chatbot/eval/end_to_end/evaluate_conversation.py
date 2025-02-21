# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from copy import deepcopy
import json
import openai
from  eval.library.llm_grader.templates import (
    prompt_template_single_criteria_full_conversation,
    prompt_template_multiple_criteria_full_conversation,
)
import os
from  eval.library.llm_grader.llm_grader import LLMgrader
import mlflow
from statistics import mean
import pandas as pd
from eval.end_to_end.constants import (
    CRITERIA_PROMPT_VAR,
    CONVO_HISTORY_VAR,
    SCENARIO_DESC_VAR,
    SCENARIO_ID_VAR,
    CONVO_ID_VAR,
    IDEAL_ANSWER_VAR,
    CONVO_ID_VAR
)
from eval.library.utils.constants import (
    PROMPT_DICT_FILE_NAME,
    RESULT_DATA_FILE_NAME,
)


METRICS_DICT_FILE_NAME = 'score_per_convo.json'
RESULTS_VAR = 'results'


class EndtoEndEval(mlflow.pyfunc.PythonModel):
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        super().__init__()

    def evaluate_single_criterion(self, json_data, prompt_dct) -> dict:
        '''Evaluate a user_nl_input against a completion given a criterion.

        Args:
            json_data (str): Please specify json data of conversation
            prompt_dct (str): Please input the dictionary of prompts

        Returns:
            dict: Evaluation results from LLM evaluator
        '''
        
        print('[ Single Criteria Outer Loop Started ]')
        all_results = []
        new_json_data = {}
        metrics_dict = {}
        print('Initialise LLM grader')
        evaluator = LLMgrader(prompt_template_single_criteria_full_conversation)
        for key, data in enumerate(json_data):
            criteria_prompt = data[CRITERIA_PROMPT_VAR]
            convo_history = data[CONVO_HISTORY_VAR]
            ideal_answer = data[IDEAL_ANSWER_VAR]
            convo_id = data[CONVO_ID_VAR]
            try:
                answer = evaluator.evaluate_conversation(convo_history, criteria_prompt)
            except openai.BadRequestError as e:
                # Extract and log the error message from the exception
                error_message = str(e)
                print(f'BadRequestError for conversation {convo_id}: {error_message}')
                
                # Set a default 'answer' value or handle the error as needed
                answer = f'{error_message}'

            if answer is None or len(answer) == 0:
                results = {'score': 0, 'explanation': 'llm evaluator did not output anything'}
            else:
                results = evaluator.validate_llm_output(answer)
                results['score'] = int(results['answer'] == ideal_answer)
            data.update(results)
            new_json_data[key] = data
            all_results.append(results)
            dict_key = 'scenario_' + str(data[SCENARIO_ID_VAR])
            if dict_key in metrics_dict.keys():
                metrics_dict[dict_key].append(results['score'])
            else:
                metrics_dict[dict_key] = [results['score']]

        for key in metrics_dict.keys():
            metrics_dict[key] = mean(metrics_dict[key])
        prompt_dct[
            'evaluator_prompt_template'
        ] = prompt_template_single_criteria_full_conversation
        print('Getting metrics')
        aveg_score = mean([x['score'] for x in all_results])

        save_path = os.path.join(self.output_folder, RESULT_DATA_FILE_NAME)
        with open(save_path, 'w') as fp:
            json.dump(new_json_data, fp, indent=4, sort_keys=True)
        
        data_list = []
        for dt in new_json_data.values():
            data_list.append(dt)
        df = pd.DataFrame.from_dict(data_list)  # type: ignore
        df = df.drop('context', axis=1, errors='ignore')
        df_per_category = (
            df.groupby(['category'])['score'].mean().reset_index()
        )
        df_per_category_dict = df_per_category.set_index('category').to_dict()['score']

        print('Logging to mlflow')
        mlflow.log_metric('avg_accuracy', aveg_score)
        mlflow.log_metrics(metrics_dict)
        mlflow.log_metrics(df_per_category_dict)
        mlflow.log_dict(metrics_dict, artifact_file=METRICS_DICT_FILE_NAME)
        mlflow.log_dict(prompt_dct, artifact_file=PROMPT_DICT_FILE_NAME)
        mlflow.log_dict(new_json_data, artifact_file=RESULT_DATA_FILE_NAME)
        print('[ Single Criteria Outer Loop Ended ]')
        return aveg_score

    def evaluate_multi_criteria(self, json_data, prompt_dct) -> dict:
        '''Evaluate a user_nl_input against a completion given a list of criteria.


        Args:
            json_data (str): Please specify json data of conversation
            prompt_dct (str): Please input the dictionary of prompts

        Returns:
            dict: Evaluation results from LLM evaluator
        '''
        print('[ Multi-Criteria Outer Loop Started ]')
        # initialize data and metric dict
        new_json_data = {}
        metrics_dict = {}
        print('Initialise LLM grader')
        # initialize evaluator
        evaluator = LLMgrader(prompt_template_multiple_criteria_full_conversation)
        full_df = pd.DataFrame(json_data)
        group_list = [
            SCENARIO_ID_VAR,
            SCENARIO_DESC_VAR,
            CONVO_ID_VAR,
            CONVO_HISTORY_VAR,
        ]
        # group data by grouplist to evaluate one conversation on all its criteria
        dfs = full_df.groupby(group_list)
        val = 0
        for keys, _ in dfs:
            df = dfs.get_group(keys)
            criteria_list = df[CRITERIA_PROMPT_VAR].to_list()
            criteria_list_string = ''
            for i in range(len(criteria_list)):
                criteria_list_string += f'{i+1}. {criteria_list[i]}\n'
            convo = df[CONVO_HISTORY_VAR].iloc[0]
            convo_id = df[CONVO_ID_VAR].iloc[0]
            try:
                answer = evaluator.evaluate_conversation(convo, criteria_list_string)
            except openai.BadRequestError as e:
                # Extract and log the error message from the exception
                error_message = str(e)
                print(f'BadRequestError for conversation {convo_id}: {error_message}')
                
                # Set a default 'answer' value or handle the error as needed
                answer = f'{error_message}'
            
            results = evaluator.validate_llm_output(answer)
            convo_scores = []
            new_item = {}
            for index, item in enumerate(results):
                item = results[item]
                item = deepcopy(item)
                ideal_answer = df[IDEAL_ANSWER_VAR].iloc[index]
                item['score'] = int(item['answer'] == ideal_answer)  # type: ignore
                convo_scores.append(item['score'])
                new_item = df.iloc[index].to_dict()
                new_item.update(item)

                new_json_data[val] = new_item
                val += 1
            metrics_dict['scenario_' + str(new_item[SCENARIO_ID_VAR])] = mean(convo_scores)

        # add the prompt of the evaluation to the list of prompts to log
        print('Getting metrics')
        prompt_dct[
            'evaluator_prompt_template'
        ] = prompt_template_multiple_criteria_full_conversation
        aveg_score = mean([x for x in metrics_dict.values()])

        # log metrics and data, and save data locally for debugging
        print('Log to mlflow')
        mlflow.log_metric('avg_accuracy', aveg_score)
        mlflow.log_metrics(metrics_dict)
        mlflow.log_dict(metrics_dict, artifact_file=METRICS_DICT_FILE_NAME)
        mlflow.log_dict(prompt_dct, artifact_file=PROMPT_DICT_FILE_NAME)
        mlflow.log_dict(new_json_data, artifact_file=RESULT_DATA_FILE_NAME)

        save_path = os.path.join(self.output_folder, RESULT_DATA_FILE_NAME)
        with open(save_path, 'w') as fp:
            json.dump(new_json_data, fp)
        print('[ Multi-Criteria Outer Loop Ended ]')
        return aveg_score
