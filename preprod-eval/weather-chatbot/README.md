# Weather chatbot

This project demonstrates a Retrieval Augmented Generation (RAG) chatbot that has been [grounded](https://techcommunity.microsoft.com/t5/fasttrack-for-azure/grounding-llms/ba-p/3843857) in an API. This example uses the Azure maps and weather API.

> Responses with GPT-3.5 Turbo were more inconsistent, for that reason it is recommended to use GPT-4o. (GPT-4 may work just as well, but it is a bit slower and more costly.)

A user may provide their geographical location of choice to the chatbot, and it will answer questions about the weather at that location.

## Setting Up the Environment

1. Create a python environment
2. Install requirements by running: 

```pip install -r requirements.txt```

3. Copy `.env.sample` as `.env` and replace all placeholder values with the correct settings from Azure Portal resources.


## Running demo.py
To run the demo from the `weather-chatbot` folder:


```bash
python -m src.demo
```

## Running Unit Tests

In the `weather-chatbot folder`, simply run this command:

```bash
pytest
```
Or, alternatively:

```bash
python -m pytest
```

## Running outer loop evaluation locally

To run the end to end evaluation from `weather-chatbot` folder:
1. Create a python environment
1. Install requirements by running **pip install -r requirements.txt**
1. Copy .env.sample as .env and replace all placeholder values with the correct settings from your Azure resources
1. In your terminal, run **python -m eval.end_to_end.run_local**


The run will create synthetic conversations between an emulated user and the assistant.
Once the run is complete, a json dataset with the results will be saved in the data folder under end_to_end.

In order to examine the results of the run in a dashboard, run **python -m streamlit run eval/end_to_end/dashboard.py**

## Running inner loop evaluation locally
### Run manual Conversation Generator

To generate conversation using the command line from `weather-chatbot` folder:

``` 
python -m eval.library.conversation_generator.command_line_tool.manual_test_case_gen_tool
```

### Run the Test Case Extractor

Start by running the conversation generator so that you have some conversations logged.

The tool extract messages from conversations. Supply the
```--agent_name YourAgentName``` parameter to name the output for your agent and the
```--agent_type YourAgentType``` parameter to identify the type. This is used to indicate the folder that
the output files should be written to: eval/agents/{agent_type}/{agent_name}/test-data/

#### Decide Which Turns to Extract From The Conversations

Opening up the generated conversations, you will see that each conversation has a conversation_id, which is a guid and each message has a message_id, which is an integer. This tool uses these two values to extract one or more messages from a conversation into a test case that you can use to evaluate your agent.
You can extract a single message from a conversation by using the integer messageId to extract:

```bash
--test_cases_to_extract "{'conversation_id': messageId}"
```

or a list of messages from a conversation:

```bash
--test_cases_to_extract "{'conversation_id': [startMessageId, nextMessageId, endMessageId]}"
```

or all messages from a conversation:

```bash
--test_cases_to_extract "{'conversation_id': *}"
```

 ...or any combination of the above (including ```--test_cases_to_extract "{'*': 3}"``` which would extract the 3rd message from ALL conversations).

Example: 
```bash
python -m eval.library.inner_loop.extract_test_cases --test_cases_to_extract "{'35fe2f005a7e4fa5be2f4e7774e1982d': 3}" --agent_type location --agent_name LocationExtractor
```

### Run the inner-loop-agent test
#### Below are examples to run the test for LocationExtractorAgent
#### You should switch to your agent_type and agent_name
#### Make sure you have "test-data" folder like this: eval\agents\location\LocationExtractor\test-data
-------------------------------------------------------------------------------------
If you want to run the test for everything
```bash
python -W "ignore" -m eval.agents.run_agent_test --agent_type location --agent_name LocationExtractor --test_data \*
```
-------------------------------------------------------------------------------------
If you want to run the test for one file under test-data
```bash
python -W "ignore" -m eval.agents.run_agent_test --agent_type location --agent_name LocationExtractor --test_data file_name.json
```
-------------------------------------------------------------------------------------
If you want to run the test for multiple files under test-data
```bash
python -W "ignore" -m eval.agents.run_agent_test --agent_type location --agent_name LocationExtractor --test_data file_name1.json file_name2.json etc.,
```
-------------------------------------------------------------------------------------
If you want to run the test for all files in one sub-folder under test-data
```bash
python -W "ignore" -m eval.agents.run_agent_test --agent_type location --agent_name LocationExtractor --test_data folder_name
```
-------------------------------------------------------------------------------------
If you want to run the test for all files in multiple sub-folders under test-data
```bash
python -W "ignore" -m eval.agents.run_agent_test --agent_type location --agent_name LocationExtractor --test_data folder_name1 folder_name2
```
-------------------------------------------------------------------------------------
If you want to run the test for one file under a sub-folder or multiple files under multiple sub-folders within test-data
```bash
python -W "ignore" -m eval.agents.run_agent_test --agent_type location --agent_name LocationExtractor --test_data folder_name1/file1.json folder_name2/file2.json
```

## Adapting the conversation generator to your own orchestrator
If you have your own orchestrator and you want to plug it in and be able to generate and evaluate conversations, here are suggested changes that need to happen:
### Modify assistantHarness.py
This file is located in weather-chatbot/eval/library/conversation_generator/assistantHarness.py
1. Import your own orchestrator and initialize it how it needs to be initialize under __init__() method. For example, some orchestrators initialize a conversation id or a session id in order to keep track of history message. You will do that in the __init__ if needed. 
1. In the get_reply() method, you need to call your orchestrator the way it needs to be called. In the case of the weather-chatbot, we are passing both the user message and the message history. Perharps for your orchestrator you may need only the user message.

### Adapting the emulated users to your orchestrator
The emulated users are built to act like users looking for weather information. You may need to update this depending on what your orchestrator does. 
1. Modify weather-chatbot/eval/library/conversation_generator/templates/customer_profile_template.py and weather-chatbot/eval/library/conversation_generator/templates/emulated_customer_templates.py to instruct it what kind of users they are and what kind of assistant they are talking to. You could get away by doing just this step and rely on supplying a scenario to the conversation generator so that it ignores the weather related attributes of the emulated user
2. Change customer profile attributes. This is a more involved update ranging over multiple files. If yoou want to create different emulated users, you have to modify their complete customer profiles for both the standard user and random user. You need to modify:
   1. weather-chatbot/eval/library/conversation_generator/customer_profile_data and update with the profile data of the user you want to emulate
   2. weather-chatbot/eval/library/conversation_generator/templates/customer_profile_template.py and update the section under Customer Profile with the new customer profile fields
   3. weather-chatbot/eval/library/conversation_generator/user_generation/data/user_profiles.json and update standard user profiles attributes to match the new user profile
   4. weather-chatbot/eval/library/conversation_generator/user_generation/random_user.py and modify to grab the new customer profile data the right way
   5. weather-chatbot/eval/library/conversation_generator/user_generation/standard_user.py and modify how the prompt is built by grabbing the new user profile attributes

After these modifications, you can head to the notebooks to try out conversation generation and conversation grading under /weather-chatbot/eval/notebooks
  
