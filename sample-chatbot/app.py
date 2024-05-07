"""
Description:
This file contains the Streamlit app that allows users to interact with the OpenAI chatbot.
The app allows users to enter a question and receive a response from the chatbot.

The app uses the ChatModel class to interact with the OpenAI API and generate responses to user questions.
The app maintains the conversation history and displays the conversation in an expander component.

The app also includes a "New Conversation" button that allows users to start a new conversation.

The app uses the Streamlit library to create the user interface and manage the app state.
The app uses the logging library to log information about the chatbot responses and conversation history.
The app uses the dotenv library to load environment variables from a .env file.
The app uses the azure-monitor-opentelemetry library to configure Azure Monitor for logging.

Environment variables:
The following environment variables need to be set in a .env file in the root directory of the project:
- API_KEY: The API key for the Azure OpenAI API.
- AZURE_ENDPOINT: The Azure OpenAI endpoint URL.
- API_VERSION: The version of the OpenAI API to use.
- DEPLOYMENT_NAME: The name of the deployment for the Azure OpenAI API.
- APPLICATIONINSIGHTS_CONNECTION_STRING: The connection string for Azure Application Insights.

Usage:
The app can be run using the following command:
streamlit run app.py
"""
import uuid
import streamlit as st
from chat_models import ChatModel
import logging
from dotenv import load_dotenv
from azure.monitor.opentelemetry import configure_azure_monitor

# Load environment variables
load_dotenv()

# Configure azure app insights and put to cache resource, so that it is only configured once
@st.cache_resource
def _configure_logging():
    configure_azure_monitor(logger_name="openai_demo_app")

# Configure logging
_configure_logging()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openai_demo_app")

# Initialize the chat model
chat_model = ChatModel(logging.getLogger("openai_demo_app.chat_model"))

# Initialize session states
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []

# Create a title for the app
st.title("Contoso Chatbot")

# Create a function to start a new chat
def new_chat():
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["input"] = ""
    st.session_state["stored_session"] = []
    logger.info("New chat started")

# Create a new chat button
if st.button("New Conversation"):
    new_chat()

# Create a text input box for the user to enter a prompt
question = st.text_input("Enter a query:", key="question")

# Create a button to generate a response
if st.button("Generate Response"):
    logger.info("Got question: " + question)
    context = None
    conversation_id = str(uuid.uuid4())
    turn_id = str(uuid.uuid4())
    for i in st.session_state["stored_session"]:
        conversation_id = i[0]
        if not context:
            context = ""
        context += "\nUser:" + i[1] + "\nBot:" + i[2] + "\n"
    response = chat_model.generate_response(question, context, conversation_id, turn_id)
    logger.info("Got response: " + response)
    logger.info("conversation_data", extra={
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "query": question,
        "response": response
    })
    st.session_state.past.append(question)
    st.session_state.generated.append(response)
    st.session_state.stored_session.append([conversation_id, question, response])
    with st.expander("Conversation", expanded=True):
        for i in range(len(st.session_state['generated'])-1, -1, -1):
            st.info(st.session_state["past"][i],icon="🧐")
            st.success(st.session_state["generated"][i], icon="🤖")