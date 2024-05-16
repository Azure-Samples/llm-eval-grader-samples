
prompt_template_single_criteria_full_conversation = """ \
You are tasked with grading a conversation based on a set of criteria. \
The conversation is between a user and a virtual assistant tasked with providing weather information. \
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
USER: I want to know weather information next Tuesday in Dallas, TX
ASSISTANT: The temperatures next Tuesday in Dallas, TX are forecasted to be highs in 90F and lows in 70F.

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
You are tasked with grading a conversation based on a set of criteria. \
The conversation is between a user and a virtual assistant tasked with providing weather information. \
Please follow the instructions below and provide JSON-formatted feedback for the criterion. \

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
1. Does the assistant give weather information?
2. Is the assistant polite in its response?

Conversation History:
USER: I want to know weather information next Tuesday in Dallas, TX
ASSISTANT: The temperatures next Tuesday in Dallas, TX are forecasted to be highs in 90F and lows in 70F.



Example Output:
{"1":
  {"criteria_prompt":"Does the assistant give weather information?", \
   "explanation": "The assistant give weather information",
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
