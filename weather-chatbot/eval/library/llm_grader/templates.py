# flake8: noqa

prompt_template_single_criteria = """\
DATA:
---------
Conversation History: {conversation}
Response: {completion}
---------

Based on the assistant's Response in the DATA field above, {criteria}
If so, respond Y. If not, respond N. Think step-by-step before assigning a grade.

Output in JSON format:  {"explanation": "<explanation here>", "answer": "<Y or N>"}.
Here an example of valid output:
'''
{"explanation": "The assistant does not ask the user's car information ",\
"answer": "N"}
'''
"""


prompt_template_single_criteria_with_reference = """\
    Respond Y or N based whether the response follows the specified rubric. \
Take into account the context, but assign the grade based only on the rubric and the response. \
Pay attention to the reference data.

Grading Rubric: {criteria}

DATA:
---------
Context: {input}
Response to Evaluate: {output}
Reference data: {reference}
---------

Think step-by-step before assigning a grade. \
Write out your explanation, then respond with Y or N on a new line."""


prompt_template_single_criteria_full_conversation = """ \
You are tasked with grading a conversation based on a set of criteria. \
The conversation is between a user and a virtual assistant at an automotive and tire company. \
The assistant is tasked with helping the user shop for tires or answering tire-related questions the user may have. \
Please follow the instructions below and provide JSON-formatted feedback for the criterion. \

DATA:
---------
Conversation History: {conversation}
---------

Criterion: {criteria}
Instructions:

1. Read the conversation history provided.
2. For the criterion, you must respond with 'Y' if true, or 'N' if false, in the form of a JSON dictionary.
3. The dictionary must include the following fields:
    "criteria_prompt": The criterion.
    "explanation": A brief explanation justifying the assigned grade.
    "answer": The grade assigned (e.g., "Y").

Example Input:
Conversation History:
USER: I want tires less than $200.
ASSISTANT: Here are the tires you asked for: Tire A, $179. Tire B, $219.

Criterion:
Does the assistant correctly recommend products within the price range specified by the user?

Example Output:
{
  "criteria_prompt": "Does the assistant correctly recommend products within the price range specified by the user?",
  "explanation": "The user asked for tires less than $200, but the assistant recommended Tire B, which costs $219, exceeding the specified price range. Therefore, the assistant did not meet the criterion, resulting in a grade of 'N'.",
  "answer": "N"
}

Ensure that the output is well-formatted. You will receive a bonus if you get this right. \
Getting the format incorrect will cause the system to crash and cost thousands of dollars. \
Provide meaningful feedback for each criterion based on the conversation's content. \
"""


prompt_template_multiple_criteria_full_conversation = """ \
You are tasked with grading a conversation based on a set of criteria.
The conversation is between a user and a virtual assistant at an automotive and tire company.
The assistant is tasked to help the user shop for tires or answer tires related questions the user may have.
Please follow the instructions below and provide JSON-formatted feedback for each criterion.

Criteria:
{criteria}

DATA:
---------
Conversation History: {conversation}
---------

Instructions:

1. Read the conversation history provided.
2. For each criterion, you must respond Y if true, or respond N if false, in the form of a JSON dictionary.
3. The dictionary must include the following fields:
    "criteria_prompt": The criteria.
    "explanation": A brief explanation justifying the assigned grade.
    "answer": The grade assigned (e.g., "Y").

--------------------------------------------------------------------
Example Input:

Criteria:
1. Does the assistant correctly recommend products within the price range specified by the user?
2. Is the assistant polite in its response?

Conversation History:
USER: I want tires less than $200.
ASSISTANT: Here are the tires you asked for: Tire A, $179. Tire B, $219.



Example Output:
{"1":
  {"criteria_prompt":"Does the assistant correctly recommend products within the price range specified by the user?", \
   "explanation": "The user asked for tires less than $200, but the assistant recommended Tire B, which costs $219, exceeding the specified price range. Therefore, the assistant did not meet the criterion, resulting in a grade of 'N'.",
   "answer": "N"},
 "2":
  {"criteria_prompt":"Is the assistant polite in its response?", \
   "explanation": "The assistant is polite and helpful, providing detailed information and answering the user's questions",\
   "answer": "Y"}
}
-----------------------------------------------------------------------
Ensure that the output is well-formatted. You will receive a bonus if you get this right. 
Getting the format incorrect will cause the system to crash and cost thousands of Dollars.
Provides meaningful feedback for each criterion based on the conversation's content. 

"""

prompt_template_single_scenario_grading = """
You are tasked with assessing whether or not a scenario took place as part of a conversation.   \
The conversation is between a customer and an assistant at an automotive and tire store. \
Please follow the instructions below and provide JSON-formatted feedback. \

Scenario:
{criteria}

DATA:
---------
Conversation History: {conversation}
---------

Instructions:
1. Read the conversation history provided.
2. For the scenario, Respond with "Y" if the scenario took place in the conversation history. Respond "N" otherwise.
3. Provide your answer in a JSON dictionary. The dictionary must include the following fields:
    "explanation": A brief explanation justifying the assigned grade.
    "answer": The grade assigned (e.g., "Y").

Example Output:
{
    "explanation": "The customer did not say they need to step away to check vehicle information",\
    "answer": "N"
}

Ensure that the output is well-formatted and provides meaningful feedback based on the conversation's content.
"""
