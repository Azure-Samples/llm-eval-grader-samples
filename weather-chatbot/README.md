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
