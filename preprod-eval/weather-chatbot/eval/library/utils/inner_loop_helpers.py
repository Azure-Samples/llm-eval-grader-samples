# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import subprocess
import re
from eval.library.llm_grader.templates import (
    prompt_template_multiple_criteria_full_conversation,
    prompt_template_single_criteria_full_conversation
)
from copy import deepcopy
from eval.library.llm_grader.llm_grader import (
    LLMgrader
)
from eval.end_to_end.constants import (
    CRITERIA_PROMPT_VAR,
    IDEAL_ANSWER_VAR,
)
from eval.end_to_end.constants import CONVO_HISTORY_VAR
    

def load_json_file(path: str, name_data: str) -> list[dict]:
    """Load JSON file and modify its contents to include source data.

    Args:
        path (str): Path to the JSON file.
        name_data (str): Name of the source data.

    Returns:
        List[dict]: List of modified JSON data.
    """
    with open(path) as json_file:
        test_data_loaded = json.load(json_file)
        modified_test_data = []
        for json_data in test_data_loaded:
            json_data['source'] = name_data
            modified_test_data.append(json_data)

        return modified_test_data

class GuardrailsGrader:
    """Use LLMgrader to grade guardrail tests using single or multi criteria 
    """
    def __init__(self, criteria: list | str, ideal_answer: list | str, 
                 agent_input: dict):
        self.criteria = criteria 
        self.ideal_answer = ideal_answer
        self.agent_input = agent_input
        
    def evaluate_single_criteria_conversation(self) -> dict:
        
        evaluator = LLMgrader(prompt_template_single_criteria_full_conversation)
        score = {}
        agent_context = self.agent_input['context']
        message_history = agent_context[CONVO_HISTORY_VAR]
        message_history = '\n'.join([f"{msg['role']}: {msg['content']}" for msg in message_history])
        answer = evaluator.evaluate_conversation(message_history, self.criteria)
        if answer is None or len(answer) == 0:
            score['exact_match'] = 0
        else:
            results = evaluator.validate_llm_output(answer)
            score["exact_match"] = int(results["answer"] == self.ideal_answer)
            score['explanation'] = results['explanation']

        return score

    def evaluate_multi_criteria_conversation(self) -> dict:
    
        evaluator = LLMgrader(prompt_template_multiple_criteria_full_conversation)
        
        criteria_list_string = ""
        for i in range(len(self.criteria)):
            criteria_list_string += f"{i+1}. {self.criteria[i]}\n"
        agent_context = self.agent_input['context']
        message_history = agent_context[CONVO_HISTORY_VAR]
        message_history = '\n'.join([f"{msg['role']}: {msg['content']}" for msg in message_history])
        answer = evaluator.evaluate_conversation(message_history, criteria_list_string)
        score = {}
        if answer is None or len(answer) == 0:
            score['exact_match'] = 0
        else:
            results = evaluator.validate_llm_output(answer)
            individual_scores = []
            individual_explanations = []
            for index, item in enumerate(results):
                item = results[item]
                item = deepcopy(item)
                ideal_answer_item = self.ideal_answer[index]
                individual_scores.append(int(item["answer"] == ideal_answer_item))
                individual_explanations.append(item['explanation'])
                score["exact_match_raw"] = individual_scores
                score['explanation'] = individual_explanations
        
        # Average the grade
        score['exact_match'] = sum(score["exact_match_raw"]) / len(score['exact_match_raw'])

        return score
    

class EvaluationUtils:
    @staticmethod
    def evaluate_agent_measure(agent_input: dict) -> dict:
        """
        Evaluates completions from a agent based on the criteria and ideal answer provided in the input.
        """
        criteria = agent_input[CRITERIA_PROMPT_VAR]
        ideal_answer = agent_input[IDEAL_ANSWER_VAR]
        guardrails_grader = GuardrailsGrader(criteria=criteria, ideal_answer=ideal_answer,
                                             agent_input=agent_input)
        if isinstance(criteria, list) and isinstance(ideal_answer, list):
            return guardrails_grader.evaluate_multi_criteria_conversation()
        elif isinstance(criteria, str) and isinstance(ideal_answer, str):
            return guardrails_grader.evaluate_single_criteria_conversation()
        else:
            # Handle other types or provide a default evaluation as required
            return {}
