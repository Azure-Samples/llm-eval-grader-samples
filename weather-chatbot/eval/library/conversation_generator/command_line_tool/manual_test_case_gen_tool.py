"""Contains code for command line tool, which can be used to generate conversation using emulated users"""
from copy import deepcopy
import urllib3
from uuid import uuid4
import os
from sys import stdin
import datetime

from eval.library.conversation_generator.conversation import ConversationGenerator
from eval.library.conversation_generator.customer_chat import CustomerChat
from eval.library.conversation_generator.command_line_tool.config import cfg
from eval.library.conversation_generator.user_generation.random_user import RandomUserGenerator
from eval.library.conversation_generator.user_generation.standard_user import StandardUserGenerator
from eval.library.conversation_generator.conversation_tools import (
    write_conversation_to_logs,
    write_conversation_to_condensed_logs,
    generate_turn,
    generate_turn_customer_message,
    generate_turn_assistant_message)

urllib3.disable_warnings()

MAIN_MENU = """Options are not case-sensitive. Here are your available options:
Enter "N" to start a new conversation.
Enter an integer N between 1 and 5 to generate N turns in the conversation.
Enter "S" during a conversation to save it to the log.
Enter "R" during a conversation to regenerate the most recent turn.
Enter "M" during the conversation to manually overwrite dialogue for the user's turn.
Enter "V" to view the whole conversation so far.
Enter "U" to view the full emulated user prompt.
Enter "C" to manually chat with assistant.  Turn generation will not be supported.
Type "help" at any time to see these options again.
Your command: """


class DummyUser():
    def __init__(self, reply: str):
        self.reply = reply

    def get_reply(self, context):
        return self.reply


class ConversationGenerationTool():
    def __init__(self):
        self.customer_chat = CustomerChat()
        self.assistantHarness = cfg['assistantHarness']
        self.customer_generator = RandomUserGenerator()
        self.cg = ConversationGenerator()

        # Create log file directory if it doesn't exist
        if not os.path.isdir(cfg['log_location']):
            os.makedirs(cfg['log_location'])

        # Create log file for this current run
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.machine_readable_log_file_name = os.path.join(cfg['log_location'], f'log_{timestamp}.txt')
        self.human_readable_log_file_name = os.path.join(cfg['log_location'], f'log_{timestamp}_condensed.xlsx')
        self.run()

    def run(self):
        """Entry point for command line tool"""
        print("Welcome to the emulated user conversation generation tool.")
        self.command = ""
        while True:
            self.route_command(self.command.strip().upper())

    def route_command(self, command: str):
        """Route main menu command to appropriate method"""
        if command == "N":
            self.new_conversation()
        elif command in ('1', '2', '3', '4', '5'):
            for i in range(int(command)):
                succeeded = self.next_turn()
                if not succeeded:
                    break
        elif command == "S":
            self.save_conversation()
        elif command == "R":
            self.regenerate_turn()
        elif command == "M":
            self.manual_entry()
        elif command == "V":
            self.view_conversation()
        elif command == "U":
            self.view_emulated_user_prompt()
        elif command == "C":
            self.chat_with_assistant()
        else:
            self.command = input(MAIN_MENU)
            return
        self.command = str(input("Your command: "))

    def get_custom_prompt(self):
        while (True):
            print('Paste your custom prompt below. Terminate entry with a blank line containing only Ctrl-D'
                  ' (or Ctrl-Z on Windows): ')
            custom_prompt = stdin.read()

            print('Prompt Received:')
            print(custom_prompt)
            command = input('Use this prompt? Type "Y" or "R" to rewrite or "A" to abort and auto-generate: ')\
                .strip().upper()

            if (command != "R"):
                if (command == "Y"):
                    return custom_prompt, True

                if (command == "A"):
                    return None, False

                print(f'Unknown command {command}')

    def new_conversation(self):
        """Initialize a customer profile and conversation"""
        # Generate customer profile
        customer_profile = self.customer_generator.generate_customer_profile()
        print(customer_profile['prompt'])
        command = input('Type "S" to switch to standard profiles. Type "G" to switch to randomly generated user '
                        'profiles. Are you OK with this customer profile? '
                        'Type "Y" or "N" or "O" to override with your own prompt: ').strip().upper()
        if command != 'Y':
            if command == 'O':
                custom_prompt, should_override_generated_profile = self.get_custom_prompt()

                if should_override_generated_profile:
                    customer_profile = {}
                    customer_profile['prompt'] = custom_prompt
                else:
                    return self.new_conversation()

            elif command == "S":
                self.customer_generator = StandardUserGenerator()
                return self.new_conversation()

            elif command == "G":
                self.customer_generator = RandomUserGenerator()
                return self.new_conversation()

            else:
                return self.new_conversation()

        # Kick off the conversation
        scenario_prompt = cfg['scenario_prompt']
        if not scenario_prompt:
            scenario_prompt = None
        self.context = {'message_history': [{'role': "assistant",
                                             'content': cfg['initial_assistant_message']}],
                        'scenario_prompt': scenario_prompt,
                        'conversation_id': uuid4().hex,
                        'customer_profile': customer_profile,
                        'assistantHarness_context': {'message_history': []}}

        # Get the first customer message
        customer_message = self.customer_chat.get_reply(self.context)
        self.context['message_history'].append({'role': 'user', 'content': customer_message})

        self.cg.print_conversation(context=self.context)

    def next_turn(self):
        # Generate turn
        try:
            succeeded = generate_turn(assistantHarness=self.assistantHarness, user=self.customer_chat, context=self.context)
        except Exception:
            # Exception may need to be handled and logged. Right now, it is only printing
            # within generate_turn
            succeeded = None

        if succeeded:
            # Print generated turn
            temp_context = deepcopy(self.context)
            temp_context['message_history'] = temp_context['message_history'][-2:]
            self.cg.print_conversation(temp_context, print_conversation_id=False)

        return succeeded

    def chat_with_assistant(self):
        self.context = {'message_history': [{'role': "assistant",
                                             'content': cfg['initial_assistant_message']}],
                        'customer_profile': {"name": "Created using manual chat with assistant",
                                             "attributes": {
                                                 "location": {}}},
                        'conversation_id': uuid4().hex,
                        'scenario_prompt': "N/A",
                        'assistantHarness_context': {'message_history': []}}

        print(f'\nASSISTANT: {cfg["initial_assistant_message"]}\n')
        self.route_chat_with_assistant_command()

    def route_chat_with_assistant_command(self):
        self.command = str(input("Your message: "))
        if self.command.lower() == "x":
            return
        elif self.command.lower() == "s":
            self.save_conversation()
            return self.route_chat_with_assistant_command()
        elif self.command.lower() == "v":
            self.view_conversation()
            return self.route_chat_with_assistant_command()
        else:
            user = DummyUser(self.command)
            generate_turn_customer_message(user=user, context=self.context)
            generate_turn_assistant_message(assistantHarness=self.assistantHarness, context=self.context)
            return self.route_chat_with_assistant_command()

    def save_conversation(self):
        write_conversation_to_logs(message_history=self.context['message_history'],
                                   conversation_id=self.context['conversation_id'],
                                   customer_profile=self.context['customer_profile'],
                                   scenario_prompt=cfg['scenario_prompt'],
                                   log_file_name=self.machine_readable_log_file_name,
                                   convo_end_reason='Ended by user of manual convo generation tool')
        print(f'Complete log saved to {self.machine_readable_log_file_name}.')
        write_conversation_to_condensed_logs(message_history=self.context['message_history'],
                                             conversation_id=self.context['conversation_id'],
                                             customer_profile=self.context['customer_profile'],
                                             log_file_name=self.human_readable_log_file_name,
                                             convo_end_reason='Ended by user of manual convo generation tool')

        print(f'Condensed log saved to {self.human_readable_log_file_name}.')

    def regenerate_turn(self):
        del self.context['message_history'][-2:]
        self.next_turn()

    def manual_entry(self):
        command = input("""You have chosen to overwrite the most recent customer message. \
Enter the new message, or enter "X" to return to the main menu: """)
        if command.strip().upper() == 'X':
            return

        # Note that this assumes there are single messages from user + assistant for a given turn.
        # Supporting structured data will require this to handle N messages from the assistant as
        # a response to a user message.
        self.context['message_history'][-1]['content'] = command
        print("You've successfully overwritten the last customer message!  New conversation history:")
        self.cg.print_conversation(context=self.context, print_conversation_id=False)

    def view_conversation(self):
        self.cg.print_conversation(self.context)

    def view_emulated_user_prompt(self):
        print(self.customer_chat.system_message)


if __name__ == '__main__':
    cgt = ConversationGenerationTool()
