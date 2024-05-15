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

To run the demo of the chatbot, execute the following command in the terminal from `src` folder:

```bash
python demo.py 
```

## Running Unit Tests

Switch to the weather-chatbot folder

```bash
pytest
```
