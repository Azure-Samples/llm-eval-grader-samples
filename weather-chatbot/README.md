# Weather chatbot

This project demonstrates API grounded RAG chatbot.

A user supposed to provide a location and the chatbot will be able to answer questions about the weather at that location.

To achieve that there are two agents: Location and Weather. The agents use external APIs to ground the information.
Location agent talks to the user about the location of interest.
Weather agent answers user's questions about the weather at the location.
The orchestrator controls the flow of the conversation invoking an agent according to the conversation state.

Each agent implements Extract Decide Reply pattern.

- Extract step extracts the necessary information from the
conversation state.
- Decide step decides what to do next.
- Reply step generates an answer for the user or generates a question if more information is required.

To run the demo of the chatbot, execute the following command in the terminal from `weather-chatbot` folder:

```bash
python -m src.demo
```

## Running Unit Tests

Switch to the weather-chatbot folder

```bash
pytest
```

## Running outer loop evaluation locally

To run the end to end evaluation from `weather-chatbot` folder:
1. Create a python environment
1. Install requirements by running **pip install -r requirements.txt**
1. Copy .env.sample as .env and replace all placeholder values with the correct settings from your Azure resources
1. In your terminal, run **python -m eval.end_to_end.run_local**
The run will create synthetic conversations between an emulated user and the assistant.
Once the run is complete, a json dataset with the results will be saved in the data folder under end_to_end

## Running inner loop evaluation locally
### Run manual Conversation Generator

To generate conversation using the command line from `weather-chatbot` folder:

1. Create a python environment
1. Install requirements by running **pip install -r requirements.txt**
1. Copy .env.sample as .env and replace all placeholder values with the correct settings from your Azure resources
1. In your terminal, run **python -m eval.library.conversation_generator.command_line_tool.manual_test_case_gen_tool**

### Run the Test Case Extractor

Start by running the conversation generator so that you have some conversations logged.

The tool extract messages from conversations. Supply the
```--component_name YourComponentName``` parameter to name the output for your component and the
```--component_type YourComponentType``` parameter to identify the type. This is used to indicate the folder that
the output files should be written to: eval/components/{component_type}/{component_name}/test-data/

#### Decide Which Turns to Extract From The Conversations

Opening up the generated conversations, you will see that each conversation has a conversation_id, which is a guid and each message has a message_id, which is an integer. This tool uses these two values to extract one or more messages from a conversation into a test case that you can use to evaluate your component.
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

 ...or any combination of the above (including ```--test_cases_to_extract "{'*': 3}"```).

Example: 
```bash
python -m src.tests.evaluation.extract_test_cases.extract_test_cases --test_cases_to_extract "{'6c868aa0db3d4d178a2441974076d933': 3}" --component_name foo
```

### Run the inner-loop-component test
#### Below are examples to run the test for LocationExtractorComponent
#### You should switch to your component_type and component_name
#### Make sure you have "test-data" folder like this: eval\components\location\LocationExtractor\test-data
-------------------------------------------------------------------------------------
If you want to run the test for everything
```bash
python -W "ignore" -m eval.components.run_component_test --component_type location --component_name LocationExtractor --test_data \*
```
-------------------------------------------------------------------------------------
If you want to run the test for one file under test-data
```bash
python -W "ignore" -m eval.components.run_component_test --component_type location --component_name LocationExtractor --test_data file_name.json
```
-------------------------------------------------------------------------------------
If you want to run the test for multiple files under test-data
```bash
python -W "ignore" -m eval.components.run_component_test --component_type location --component_name LocationExtractor --test_data file_name1.json file_name2.json etc.,
```
-------------------------------------------------------------------------------------
If you want to run the test for all files in one sub-folder under test-data
```bash
python -W "ignore" -m eval.components.run_component_test --component_type location --component_name LocationExtractor --test_data folder_name
```
-------------------------------------------------------------------------------------
If you want to run the test for all files in multiple sub-folders under test-data
```bash
python -W "ignore" -m eval.components.run_component_test --component_type location --component_name LocationExtractor --test_data folder_name1 folder_name2
```
-------------------------------------------------------------------------------------
If you want to run the test for one file under a sub-folder or multiple files under multiple sub-folders within test-data
```bash
python -W "ignore" -m eval.components.run_component_test --component_type location --component_name LocationExtractor --test_data folder_name1/file1.json folder_name2/file2.json
```
