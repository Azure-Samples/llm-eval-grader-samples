# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Description: This script is used to populate the data in the Streamlit app.

The script reads the test data from the questions.csv file and runs the Streamlit app for each conversation in the test data.
For each conversation, the script enters the questions from the test data and clicks the button to generate responses from the chatbot.
"""
from streamlit.testing.v1 import AppTest
import pandas as pd

# Read Test Data
test_data = pd.read_csv("questions.csv")
test_data = test_data.sort_values("turn_specific_sequence_id")
print(test_data.shape)
grouped = test_data.groupby("conversation")

for name, group in grouped:
    # Run the app for each conversation
    at = AppTest.from_file("app.py")
    at.run(timeout=1200)
    for index, row in group.iterrows():
        # Enter the question and click the button
        at.text_input[0].input(row["question"]).run()
        at.button[1].click().run(timeout=1200)
