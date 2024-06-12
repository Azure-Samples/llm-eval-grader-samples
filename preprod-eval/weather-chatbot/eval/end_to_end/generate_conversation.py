from eval.library.conversation_generator.user_generation.standard_user import (
    StandardUserGenerator,
)
from eval.library.conversation_generator.conversation import (
    ConversationGenerator,
)
from eval.library.utils.eval_helpers import get_conversation_as_string
from eval.end_to_end.constants import (
    CONVO_ID_VAR,CONVO_HISTORY_VAR,SCENARIO_DESC_VAR,SCENARIO_ID_VAR,
    LOCAL_END_TO_END_DATAPATH,LOCAL_SCENARIO_DATAPATH,CONVO_DATA_FILE_NAME,
    LOCAL_COPILOT_PRINCIPLES_DATAPATH,CONVO_RUNTIME_FILE_NAME,CUSTOMER_PROFILE_VAR,
    EXIT_ERROR_VAR,CONVO_GEN_RETRY_VAR,PROFILE_OVERRIDE_VAR,NUM_CONVO_VAR,USER_PROMPT_VAR
)
import pandas as pd
import mlflow
import json
import os
import time


class OrchestrateConversation:
    def __init__(self, convo_gen: ConversationGenerator, default_num_convo=3):
        self.convo_gen_retry_limit = 0
        self.convo_gen_retry = 0
        self.structured_convo_data_list = []
        self.default_num_convo = default_num_convo
        self.scenario_and_retry_dict = {}
        self.convo_gen = convo_gen
        self.copilot_principles = pd.read_csv(LOCAL_COPILOT_PRINCIPLES_DATAPATH)
        self.runtime_dict = {}
        self.scenario_count = 0

    def initialize_scenario_criteria_df(self) -> pd.DataFrame:
        '''This method is to download the scenario criteria csv from azure machine learning blob workspace
        Returns:
            pd.DataFrame: Dataframe of scenarios and criteria
        '''
        scenario_df = pd.read_csv(LOCAL_SCENARIO_DATAPATH)
        if scenario_df is None:
            raise RuntimeError('Found 0 scenarios in path: {LOCAL_SCENARIO_DATAPATH}')
        scenario_df[NUM_CONVO_VAR] = scenario_df[
            NUM_CONVO_VAR
        ].fillna(0)
        scenario_df.profile_overrides = scenario_df.profile_overrides.fillna('')
        scenario_df.user_prompt = scenario_df.user_prompt.fillna('')

        return scenario_df

    def generate_scenario_convo_dict_helper(
        self, df: pd.DataFrame, context: dict, customer_profile: dict
    ) -> list[dict]:
        '''This methods takes in a dataframe a scenario and its criteria and returns a list
        of dict of each scenario criteria pair.
        Args:
            df (pd.Dataframe): Dataframe with headers [scenario_id,scenario_desc,criteria_id,
                criteria_name,criteria_prompt,ideal_answer,num_convo_to_generate]
            context (dict): generated conversation context
            customer_profile (dict): generated customer profile
        Returs:
            (list): list of dict for each scenario criteria pair
        '''
        message_history_string = get_conversation_as_string(context)
        scenario_conversation_json = []
        for _, row in df.iterrows():
            new_dict = row.to_dict()
            new_dict[CONVO_ID_VAR] = context[CONVO_ID_VAR]
            new_dict[CONVO_HISTORY_VAR] = message_history_string
            new_dict[CUSTOMER_PROFILE_VAR] = customer_profile
            new_dict[EXIT_ERROR_VAR] = str(self.convo_gen.exit_due_to_error)
            new_dict[CONVO_GEN_RETRY_VAR] = self.convo_gen_retry
            scenario_conversation_json.append(new_dict)
        scen_id = df[SCENARIO_ID_VAR].iloc[0]
        scen_desc = df[SCENARIO_DESC_VAR].iloc[0]
        # Append copilot principles criteria
        criterias = self.copilot_principles
        for _, row in criterias.iterrows():
            new_dict = row.to_dict()
            new_dict[SCENARIO_ID_VAR] = int(scen_id)
            new_dict[SCENARIO_DESC_VAR] = str(scen_desc)
            new_dict[CONVO_ID_VAR] = context[CONVO_ID_VAR]
            new_dict[CONVO_HISTORY_VAR] = message_history_string
            new_dict[CUSTOMER_PROFILE_VAR] = customer_profile
            new_dict[EXIT_ERROR_VAR] = str(self.convo_gen.exit_due_to_error)
            new_dict[CONVO_GEN_RETRY_VAR] = self.convo_gen_retry
            scenario_conversation_json.append(new_dict)
        return scenario_conversation_json

    def generate_structured_convo_data_per_scenario(
        self, group: tuple, df: pd.DataFrame
    ) -> None:
        '''This method is to generate structured convo data per scenario
        by taking input scenario to generate a conversation and store this
        along with its criteria as a json into a structured convo data list
        Args:
            group (tuple): Scenario Description and Profile overrides
            df (pd.DataFrame): Dataframe with headers [scenario_id,scenario_desc,criteria_id,
            criteria_name,criteria_prompt,ideal_answer,num_convo_to_generate]

        Returns: None

        '''
        scenario_desc = group[0]
        profile_overrides = group[1]
        user_prompt = group[2]
        customer_generator = StandardUserGenerator()
        if profile_overrides:
            customer_generator.all_valid_profiles(json.loads(profile_overrides))
        customer_profile = customer_generator.generate_customer_profile()
        if user_prompt:
            customer_profile[USER_PROMPT_VAR] = str(user_prompt)
        context = self.convo_gen.generate_conversation(
            customer_profile=customer_profile, scenario_prompt=scenario_desc
        )

        scenario_happened = True  # we will not be assessing scenario for now
        if scenario_happened:
            scenario_convo_dict = self.generate_scenario_convo_dict_helper(
                df, context, customer_profile
            )
            self.structured_convo_data_list.extend(scenario_convo_dict)
            self.scenario_and_retry_dict[df[SCENARIO_ID_VAR].iloc[0]] = (
                self.convo_gen_retry
            )
        elif self.convo_gen_retry in range(self.convo_gen_retry_limit):
            print(f'retry generating convo for this scenario: {scenario_desc}')
            self.convo_gen_retry += 1
            self.generate_structured_convo_data_per_scenario(group, df)
        else:
            print(f'Scenario did not play out : {scenario_desc}')
            self.convo_gen_retry = -1
            scenario_convo_dict = self.generate_scenario_convo_dict_helper(
                df, context, customer_profile
            )
            self.structured_convo_data_list.extend(scenario_convo_dict)
            self.scenario_and_retry_dict[df[SCENARIO_ID_VAR].iloc[0]] = (
                self.convo_gen_retry
            )
        self.convo_gen_retry = 0

    def generate_structured_convo_data_list(self) -> None:
        '''This method is to generate a scenario list from azure machine learning blob,
        and activate the conversation with the specific scenario from scenario list'''
        scenario_df = self.initialize_scenario_criteria_df()

        total_runtime = 0
        index = 0
        # Loop each scenario from the dataframe to generate conversation
        for group, df in scenario_df.groupby(
            [SCENARIO_DESC_VAR, PROFILE_OVERRIDE_VAR, USER_PROMPT_VAR]
        ):
            index += 1
            scenario_start_time = time.time()
            num_convo = df[NUM_CONVO_VAR].iloc[0]
            if num_convo <= 0:
                num_convo = self.default_num_convo
            for _ in range(num_convo):
                self.generate_structured_convo_data_per_scenario(group, df)
            scenario_end_time = time.time()
            scenario_runtime = scenario_end_time - scenario_start_time
            scenario_desc = str(group[0])
            self.runtime_dict[scenario_desc] = scenario_runtime
            print('[', index, '] scenario_desc:', scenario_desc)
            print('single scenario runtime: ', scenario_runtime, 'seconds\n')
            total_runtime += scenario_runtime
        print('total runtime: ', total_runtime, '[scenario count:', index, ']')
        self.scenario_count = index
        self.runtime_dict['total_runtime'] = total_runtime

    def log_artifacts(self, artifacts):
        '''log generated convo and token usage'''
        
        mlflow.log_dict(artifacts['generated_convo'], artifact_file=CONVO_DATA_FILE_NAME)
        mlflow.log_dict(self.runtime_dict, artifact_file=CONVO_RUNTIME_FILE_NAME)
        save_path = os.path.join(LOCAL_END_TO_END_DATAPATH, CONVO_DATA_FILE_NAME)
        os.makedirs(LOCAL_END_TO_END_DATAPATH, exist_ok=True)

        # save for local debugging if needed
        with open(save_path, 'w') as fp:
            json.dump(artifacts['generated_convo'], fp)

    def generate_conversation(self):
        '''This function generates conversations for the end to end run.
        Returns:
            dict: Evaluation Data for LLM evaluator
        '''
        self.generate_structured_convo_data_list()
        generated_convo = self.structured_convo_data_list
        artifacts = {}

        artifacts['generated_convo'] = generated_convo

        self.log_artifacts(artifacts)

        return generated_convo
