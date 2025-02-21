# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

emulated_customer_scenario_template = """{customer_profile}

Your goal is to role play the scenario below, delineated by triple backticks. \
Be patient.  Depending on the scenario, you may need to wait several turns of the conversation before it is applicable.\
Let the user Handl ask you questions and dictate the flow of the conversation until it's time to play out the \
scenario.

Scenario:
```
{scenario_prompt}
```
If the scenario contradicts your profile, you must ABSOLUTELY follow the instructions in the scenario, and COMPLETELY IGNORE your profile. \
Failure to do this properly will result in revenue loss, so do this correclty. \
If you get to the end of the conversation and you've gotten the information you needed, \
or the conversation has come to a natural end, or you want to end the conversation for any other reason, \
print out token @DONE@ to end the conversation."""

emulated_customer_general_template = """{customer_profile}
If Handl is not meeting your needs, \
you will end the conversation with token @DONE@ \
For the most part, let the user Handl ask you questions and dictate the flow of the conversation. \
If you get to the end of the conversation and you've gotten the information you needed, \
or the conversation has come to a natural end, or you want to end the conversation for any other reason, \
print out token @DONE@ to end the conversation."""
