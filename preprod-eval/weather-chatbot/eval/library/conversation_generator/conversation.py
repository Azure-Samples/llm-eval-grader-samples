# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""This file contains the tools required to generate and assess conversations between an emulated user trying
to act out a scenario, and the prompt orchestrator."""

from eval.library.conversation_generator.customer_chat import (
    CustomerChat,
)
from eval.library.conversation_generator.assistantHarness import (
    OrchestratorHarness,
)
from eval.library.conversation_generator.conversation_tools import (
    generate_turn,
    write_conversation_to_logs,
    write_conversation_to_condensed_logs)

from eval.library.utils.eval_helpers import (
    get_conversation_as_string,
)
from eval.library.llm_grader.templates import (
    prompt_template_single_scenario_grading,
)
from eval.library.llm_grader.llm_grader import LLMgrader

from typing import Optional, Tuple
from uuid import uuid4
from copy import deepcopy
import json
import os
from datetime import datetime
import traceback

CONVO_DATA_FILE_NAME = "generated_conversation.json"
LOCAL_END_TO_END_DATAPATH = "eval/end_to_end/data"


class ConversationGenerator:
    """Object for generate conversations between emulated users and the assistantHarness"""

    def __init__(self, max_turns=8):
        self.customer_chat = CustomerChat()
        self.assistantHarness = OrchestratorHarness()
        self.max_turns = max_turns
        self.exit_due_to_error = ""

    def initialize_context(
        self, context: dict, scenario_prompt: str, customer_profile: dict
    ) -> dict:
        # Add to context for record-keeping
        context["scenario_prompt"] = scenario_prompt
        context["conversation_id"] = uuid4().hex
        context["customer_profile"] = customer_profile
        context["assistantHarness_context"] = {"message_history": []}

        print('------------------------------')
        print(f'Conversation_id: {context["conversation_id"]}')
        print('------------------------------')
        # Get the first customer message if it's required
        if context["message_history"][-1]["role"] == "assistant":
            customer_message = self.customer_chat.get_reply(context)
            context["message_history"].append(
                {"role": "user", "content": customer_message}
            )
        return context

    def generate_test_case(
        self,
        scenario_prompt: str,
        customer_profile: dict,
        end_of_test_case_key: Optional[str] = None,
        context: dict = {
            "message_history": [
                {
                    "role": "assistant",
                    "content": "Hello! How can I help you?",
                }
            ]
        },
    ) -> Tuple[dict, str]:
        # Ensure that context resets with each conversation
        context = deepcopy(context)

        context = self.initialize_context(context, scenario_prompt, customer_profile)


        # Carry out the conversation
        convo_end_reason = 'max_turns'
        first_assistant_message = context["message_history"][0]["content"]
        first_user_message = context["message_history"][1]["content"]
        print(f'\nASSISTANT: {first_assistant_message}\n')
        print(f'\nUSER: {first_user_message}\n')
        for _ in range(self.max_turns - 1):
            try:
                context = self.generate_turn(context)
            except Exception:
                e = traceback.format_exc()
                print("An error occured", e)
                self.exit_due_to_error = f"An error occured: {e}"
                break

            # Detect when to end the conversation
            if self.test_case_interrupter(context, end_of_test_case_key):
                convo_end_reason = f'End of test case key {end_of_test_case_key} found in assistantHarness_context'
                break
            elif self.conversation_interrupter(context):
                convo_end_reason = 'User-ending-conversation keyword found'
                break

        return context, convo_end_reason

    def generate_conversation(
        self,
        customer_profile: dict,
        scenario_prompt: str = "",
        context: dict = {
            "message_history": [
                {
                    "role": "assistant",
                    "content": "Hello! How can I help you?",
                }
            ]
        },
    ) -> dict:
        # Ensure that context resets with each conversation
        context = deepcopy(context)
        if "user_prompt" in customer_profile.keys():
            context["message_history"].append({
                "role": "user",
                "content": customer_profile["user_prompt"],
            })

        # Generate a unique customer if none provided
        context = self.initialize_context(context, scenario_prompt, customer_profile)

        # Carry out the conversation
        print("[ Conversation Started ]")
        first_assistant_message = context["message_history"][0]["content"]
        first_user_message = context["message_history"][1]["content"]
        print(f'\nASSISTANT: {first_assistant_message}\n')
        print(f'\nUSER: {first_user_message}\n')
        for turn in range(self.max_turns - 1):
            # The assistantHarness is currently breaking. Putting this try catch until it's fixed
            try:
                context = self.generate_turn(context)
            except Exception:
                e = traceback.format_exc()
                print("An error occured", e)
                self.exit_due_to_error = f"An error occured: {e}"
                break

            # Base on current storing conversation mechanism,
            # we store one assistant message then one customer message in one conversation loop.
            # so we will do the conversation interrupter at the end of each loop.
            # If later on, we change the conversation storing mechanism to enable to store multiple assistant messages,
            # and/or multiple customer messages at each loop. then we will change the conversation interrupter from
            # only one at the end of each loop, to one after assistant_message(s), and one after customer_message(s).

            # Detect when to end the conversation
            if self.conversation_interrupter(context) is True:
                # To log we end the conversation by conversation interrupter
                print("...Conversation Ending Interrupt...\n")
                break

            print("Conversation Cont...")
            if turn == self.max_turns - 2:
                max_turn_warning_message = (
                    "...This is turn "
                    + str(turn + 1)
                    + ", and next turn will reach the max_turns,\n"
                    + "we set for this conversations. Please start a new session for your question. Thank you:)\n"
                )
                print(max_turn_warning_message)

        return context

    def generate_turn(self, context: dict) -> dict:
        # Generate turn
        generate_turn(assistantHarness=self.assistantHarness, user=self.customer_chat, context=context)
        return context

    def test_case_interrupter(self, context, end_of_test_case_key=None):
        """Interrupt test case when key is found in context"""
        if end_of_test_case_key in context["assistantHarness_context"]:
            return True
        return False

    def conversation_interrupter(self, context):
        """There are 2 major way to do conversation interrupt, one is do keyword matching,
        which finds the most common conversation ending keywords and sentences and flag the conversation to interrupt.
        Another is sending the conversation to LLM and let it analyzes if the conversation comes to the end,
        but this apporach will increase the llm usage, extra resources need it."""

        user_content = str(context["message_history"][-1]["content"]).lower()
        user_ending_conversation_keyword = ["@done@"]
        for keyword in user_ending_conversation_keyword:
            if (user_content.find(keyword) != -1):
                return True
        # We need to interrupt a conversation if assisatant starts repeating itself
        last_assistant_reply = str(context["message_history"][-2]["content"]).lower()
        second_to_last_assistant_reply = str(context["message_history"][-4]["content"]).lower()
        if last_assistant_reply == second_to_last_assistant_reply:
            self.exit_due_to_error = "Conversation Interrupted: Repeating response (assistant)"
            return True
        last_user_reply = str(context["message_history"][-1]["content"]).lower()
        second_to_last_user_reply = str(context["message_history"][-3]["content"]).lower()
        if last_user_reply == second_to_last_user_reply:
            self.exit_due_to_error = "Conversation Interrupted: Repeating response (User)"
            return True
        return False

    def assess_conversation(self, context, scenario) -> dict | None:
        """Detect whether or not the scenario played out as expected"""
        evaluator = LLMgrader(prompt_template_single_scenario_grading)
        convo_history = get_conversation_as_string(context)
        answer = evaluator.evaluate_conversation(convo_history, scenario)
        results = evaluator.validate_llm_output(answer)
        return results

    def print_conversation(self, context, print_conversation_id=True) -> None:
        if print_conversation_id:
            print(f"Conversation Id: {context['conversation_id']}")
        for turn_dct in context["message_history"]:
            print(f"{turn_dct['role'].upper()}: {turn_dct['content']}")
            
    def save_conversation(self, context, log_location, scenario_prompt=''):
        # Create log file directory if it doesn't exist
        if not os.path.isdir(log_location):
            os.makedirs(log_location)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        machine_readable_log_file_name = os.path.join(log_location, f'log_{timestamp}.txt')
        human_readable_log_file_name = os.path.join(log_location, f'log_{timestamp}_condensed.xlsx')
        write_conversation_to_logs(message_history=context['message_history'],
                                conversation_id=context['conversation_id'],
                                customer_profile=context['customer_profile'],
                                scenario_prompt=scenario_prompt,
                                log_file_name=machine_readable_log_file_name,
                                convo_end_reason='Ended by user of manual convo generation tool')
        print(f'Complete log saved to {machine_readable_log_file_name}.')
        write_conversation_to_condensed_logs(message_history=context['message_history'],
                                            conversation_id=context['conversation_id'],
                                            customer_profile=context['customer_profile'],
                                            log_file_name=human_readable_log_file_name,
                                            convo_end_reason='Ended by user of manual convo generation tool')

        print(f'Condensed log saved to {human_readable_log_file_name}.')
