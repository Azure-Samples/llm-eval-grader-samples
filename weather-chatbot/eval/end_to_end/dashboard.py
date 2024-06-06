import streamlit as st
import json
import pandas as pd
import os

from eval.end_to_end.constants import (
    CRITERIA_NAME_VAR,
    LOCAL_END_TO_END_DATAPATH,
    CRITERIA_ID_VAR,
    CRITERIA_PROMPT_VAR,
    CONVO_ID_VAR,
    CONVO_HISTORY_VAR,
    SCENARIO_ID_VAR,
    SCENARIO_DESC_VAR,
)
from eval.library.utils.constants import (
    RESULT_DATA_FILE_NAME,
)


def main():
    data_path = os.path.join(LOCAL_END_TO_END_DATAPATH, RESULT_DATA_FILE_NAME)
    with open(data_path, 'rb') as f:
        data = json.load(f)

    data_list = []
    for dt in data.values():
        data_list.append(dt)

    df = pd.DataFrame.from_dict(data_list)  # type: ignore
    df = df.drop('context', axis=1, errors='ignore')
    df.to_csv("data_with_results.csv")
    st.write("# Display Dataset")
    st.write(df)

    st.write("## Summary")
    st.write(f"Number of conversation: {len(df)}")
    st.write(f"Number of scenarios: {df[SCENARIO_ID_VAR].nunique()}")
    st.write(f"Average score: {df['score'].mean()}")

    st.write("## Results per Category")
    df_per_category = (
        df.groupby(["category"])["score"].mean().reset_index()
    )
    st.write(df_per_category)

    "## Filter Results"

    sort_by_item = st.selectbox(
        "Scenario or Criteria",
        options=[SCENARIO_ID_VAR, CRITERIA_ID_VAR],
    )
    if sort_by_item == SCENARIO_ID_VAR:
        df_filter = (
            df.groupby([SCENARIO_ID_VAR, SCENARIO_DESC_VAR])["score"].mean().reset_index()
        )
        st.write(f"Results per {sort_by_item}")
        st.write(df_filter)
        scenario_id = st.selectbox(
            "Scenario",
            options=df_filter[SCENARIO_ID_VAR].unique().tolist(),
        )
        
        scenario_df = df[df[SCENARIO_ID_VAR] == int(scenario_id)]  # type: ignore
        scenario_score = st.selectbox(
            "Scenario Score",
            options=scenario_df["score"].unique().tolist(),
        )
        scenario_df = scenario_df[scenario_df["score"] == int(scenario_score)]  # type: ignore
        st.write(scenario_df)
        average_score = scenario_df["score"].mean()
        st.write(f"Scenario Description: {scenario_df[SCENARIO_DESC_VAR].iloc[0]}")
        st.write(f"Average Score: {average_score}")
        "### Display a conversation from the scenario"
        convo_id = st.selectbox("Conversation", options=scenario_df[CONVO_ID_VAR].unique().tolist())

        convo_df = scenario_df[scenario_df[CONVO_ID_VAR] == convo_id]

        criteria = st.selectbox("Criteria", options=convo_df[CRITERIA_ID_VAR].unique().tolist())
        criteria_df = convo_df[convo_df[CRITERIA_ID_VAR] == criteria]
        st.write(criteria_df)
        msg = "<p>" + criteria_df[CONVO_HISTORY_VAR].iloc[0].replace("\n", "<br />") + "<p/>"
        st.markdown(f"{msg}", unsafe_allow_html=True)

        st.write(f"Criteria Prompt: {criteria_df[CRITERIA_PROMPT_VAR].iloc[0]}")
        st.write(f"Score: {criteria_df['score'].iloc[0]}")
        st.write(f"Conversation Generation retry Count: {criteria_df['convo_gen_retry'].iloc[0]}")
        st.write(f"Score Explaination: {criteria_df['explanation'].iloc[0]}")
    else:
        df_filter = (
            df.groupby([CRITERIA_ID_VAR, CRITERIA_NAME_VAR, CRITERIA_PROMPT_VAR])["score"].mean().reset_index()
        )
        st.write(f"Results per {sort_by_item}")
        st.write(df_filter)
        criteria_id = st.selectbox(
            "Criteria",
            options=df_filter[CRITERIA_ID_VAR].unique().tolist(),
        )
        criteria_df = df[df[CRITERIA_ID_VAR] == int(criteria_id)]  # type: ignore
        criteria_score = st.selectbox(
            "Criteria Score",
            options=criteria_df["score"].unique().tolist(),
        )
        criteria_df = criteria_df[criteria_df["score"] == int(criteria_score)]  # type: ignore
        st.write(criteria_df)
        average_score = criteria_df["score"].mean()
        st.write(f"Criteria Description: {criteria_df[CRITERIA_PROMPT_VAR].iloc[0]}")
        st.write(f"Average Score: {average_score}")
        "### Display a conversation from the scenario"
        convo_id = st.selectbox("Conversation", options=criteria_df[CONVO_ID_VAR].unique().tolist())

        convo_df = criteria_df[criteria_df[CONVO_ID_VAR] == convo_id]

        scenario = st.selectbox("Scenario", options=convo_df[SCENARIO_ID_VAR].unique().tolist())
        scenario__df = convo_df[convo_df[SCENARIO_ID_VAR] == scenario]
        st.write(scenario__df)
        msg = "<p>" + scenario__df[CONVO_HISTORY_VAR].iloc[0].replace("\n", "<br />") + "<p/>"
        st.markdown(f"{msg}", unsafe_allow_html=True)

        st.write(f"Scenario Prompt: {scenario__df[SCENARIO_DESC_VAR].iloc[0]}")
        st.write(f"Score: {scenario__df['score'].iloc[0]}")
        st.write(f"Conversation Generation retry Count: {scenario__df['convo_gen_retry'].iloc[0]}")
        st.write(f"Score Explaination: {scenario__df['explanation'].iloc[0]}")
        st.write(f"Exit due to  Error: {scenario__df['exit_due_to_error'].iloc[0]}")


if __name__ == "__main__":
    main()
