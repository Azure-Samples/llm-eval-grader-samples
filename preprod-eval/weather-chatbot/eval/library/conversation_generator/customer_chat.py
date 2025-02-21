# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""This file contains the CustomerChat object.  It is used to generate the emulated user side of the conversation"""
from eval.library.conversation_generator.templates.emulated_customer_templates import (
    emulated_customer_scenario_template,
    emulated_customer_general_template)

from copy import deepcopy
from eval.library.utils.llm_interface import get_completion


class CustomerChat:
    """Emulated user chat generation object"""
    def __init__(self):
        self.temperature = 0.7

    def get_system_message(self, context: dict) -> str:
        # If context contains a scenario, try to carry it out
        if 'scenario_prompt' in context:
            return emulated_customer_scenario_template.format(
                customer_profile=context['customer_profile']['prompt'],
                scenario_prompt=context['scenario_prompt'])
        else:
            return emulated_customer_general_template.format(
                customer_profile=context['customer_profile']['prompt'])

    def get_reply(self, context: dict) -> str | None:
        system_message = self.get_system_message(context)

        # Walk the message history and create the history
        # for the emulated user
        messages = []

        if len(system_message) > 0:
            messages.append({'role': 'system', 'content': system_message})

        for message in context['message_history']:
            cleaned_message = deepcopy(message)
            if 'context' in cleaned_message:
                del cleaned_message['context']

            # Flip the roles around because this bot is playing the user
            if cleaned_message['role'] == 'user':
                cleaned_message['role'] = 'assistant'
            elif cleaned_message['role'] == 'assistant':
                cleaned_message['role'] = 'user'

            messages.append(cleaned_message)

        # print('-------------------------------------------------------------')
        # print('Emulated User message history')
        # print(messages)
        # print('-------------------------------------------------------------')
        
        response = get_completion(
            messages=messages,
            temperature=self.temperature,
        )

        return response
