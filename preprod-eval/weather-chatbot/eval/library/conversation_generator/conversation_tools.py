import os
from typing import List, Optional
import json
import pandas as pd
from copy import deepcopy


def write_conversation_to_logs(message_history: List,
                               conversation_id: str,
                               customer_profile: dict,
                               scenario_prompt: str,
                               log_file_name: str,
                               convo_end_reason: str,
                               test_result: Optional[dict] = {}):
    formatted_json = {
        'conversation_id': conversation_id,
        'conversation_history': [],
        'customer_profile': customer_profile,
        'scenario_prompt': scenario_prompt,
        'convo_end_reason': convo_end_reason
    }
    if test_result:
        formatted_json['test_result'] = test_result

    message_id = 1
    for msg in message_history:
        # Add message id
        msg['messageId'] = message_id

        # Message history should contain messages up to, but not including the current message
        if 'context' in msg:
            msg['context']['message_history'] = msg['context']['message_history'][:-1]
        formatted_json['conversation_history'].append(msg)

        message_id = message_id + 1

    with open(log_file_name, 'a') as f:
        f.write('\n')
        f.write("~~~NEW_CONVERSATION~~~")
        f.write('\n')
        json.dump(formatted_json, f, indent=4)


def write_conversation_to_condensed_logs(message_history: List,
                                         conversation_id: str,
                                         customer_profile: dict,
                                         log_file_name: str,
                                         convo_end_reason: str,
                                         test_result: Optional[dict] = {}):

    # Base columns (always present)
    log_dict = {
        'conversation_id': [],
        'messageId': [],
        'role': [],
        'message': []
    }

    # Other context keys to look for
    possible_context_keys = [
        'visited_agents',
        'city',
        'state',
        'zip_code',
        'location_details'
    ]

    # Initialize flags for presence of contexts key
    new_col_flag = {}
    for key in possible_context_keys:
        new_col_flag[key] = False
        log_dict[key] = []

    message_id = 1
    for msg in message_history:
        # Append base info
        log_dict['conversation_id'].append(conversation_id)
        log_dict['messageId'].append(message_id)
        log_dict['role'].append(msg['role'])
        log_dict['message'].append(msg['content'])
        # Append context info
        if 'context' in msg:
            for key in possible_context_keys:
                if key in msg['context']:
                    new_col_flag[key] = True
                else:
                    log_dict[key].append(None)
        else:
            for key in possible_context_keys:
                log_dict[key].append(None)

        message_id = message_id + 1

    # Convert dict to df
    df_log = pd.DataFrame(log_dict)
    if df_log.loc[len(df_log.index) - 1, 'role'] == 'user':
        df_log = df_log[:-1]

    # Add expected location details column beside location details where appropriate
    expected_location_details = customer_profile['attributes']['location']
    # filt_visited_location_id = (df_log['visited_agents'].astype(str).str.contains('LocationAgent'))
    filt_location_identified = (df_log['location_details'].notnull())
    # filt_add_expected_location_details = filt_visited_location_id & filt_location_identified
    filt_add_expected_location_details = filt_location_identified
    df_log.loc[:, 'expected_location_details'] = ""
    if filt_add_expected_location_details.any():
        df_log.loc[filt_add_expected_location_details, 'expected_location_details'] = str(expected_location_details)

    # Drop columns with all nulls
    for col in possible_context_keys:
        if df_log[col].isnull().all():
            df_log = df_log.drop(columns=col)

    # Add test result to last row of convo
    if test_result:
        df_log['test_result'] = ""
        df_log.loc[df_log.index[-1], 'test_result'] = str(test_result)

    df_log['convo_end_reason'] = ""
    df_log.loc[df_log.index[-1], 'convo_end_reason'] = convo_end_reason

    # Enable multi-convo logs
    if os.path.exists(log_file_name):
        df_log_existing = pd.read_excel(log_file_name, engine='openpyxl')
        df_log = pd.concat([df_log_existing, df_log], axis=0)

    if 'location_details' in df_log.columns:
        df_log = _make_cols_adjacent(df_log, 'location_details', 'expected_location_details')

    # Write to Excel
    _write_df_to_excel(df_log, log_file_name)


def generate_turn(assistantHarness, user, context: dict) -> bool:
    success_bool = generate_turn_assistant_message(assistantHarness, context=context)
    if not success_bool:
        return success_bool

    # Get customer message and log it
    generate_turn_customer_message(user, context=context)
    return success_bool


def generate_turn_customer_message(user, context: dict):
    # Get customer message and log it
    customer_message = user.get_reply(context)
    print(f'\nUSER: {customer_message}\n')
    context['message_history'].append({'role': 'user', 'content': customer_message})


def generate_turn_assistant_message(assistantHarness, context: dict) -> bool:
    # Get a snapshot of the message history in the assistantHarness context before it can be modified
    last_turn_assistantHarness_context_message_history = deepcopy(context['assistantHarness_context']['message_history'])

    # Generate turn
    assistant_message = assistantHarness.get_reply(context)

    print(f'\nASSISTANT: {assistant_message}\n')

    # We must modify the message history to accurately log the message history used by the assistant
    # This is because the assistant can truncate message_history at any time
    # Start with the assistantHarness_context from last turn
    new_assistantHarness_context = deepcopy(context['assistantHarness_context'])
    new_assistantHarness_context['message_history'] = last_turn_assistantHarness_context_message_history

    # Then add the latest user message and newly generated assistant message
    last_user_message = deepcopy(context['message_history'][-1])
    new_assistantHarness_context['message_history'].append(last_user_message)
    new_assistantHarness_context['message_history'].append({'role': 'assistant', 'content': assistant_message})

    # Log this reconstructed context as the assistantHarness_context for this turn
    context['message_history'].append(
        {'role': 'assistant', 'content': assistant_message, 'context': new_assistantHarness_context})
    context['assistantHarness_context'] = new_assistantHarness_context

    if assistant_message is None:
        return False
    return True


def _make_cols_adjacent(df, col1, col2):

    cols = df.columns
    ind_col1 = (cols == col1).argmax()
    ind_col2 = (cols == col2).argmax()

    if ind_col1 < ind_col2:
        newcols = cols[:ind_col1].tolist() + \
            [cols[ind_col1]] + \
            [cols[ind_col2]] + \
            cols[ind_col1 + 1:ind_col2].tolist() + \
            cols[ind_col2 + 1:].tolist()
    else:
        newcols = cols[:ind_col2].tolist() + \
            [cols[ind_col1]] + \
            [cols[ind_col2]] + \
            cols[ind_col2 + 1:ind_col1].tolist() + \
            cols[ind_col1 + 1:].tolist()
    return df[newcols]


def _write_df_to_excel(df, excel_filename):

    df = df.reset_index(drop=True)
    writer = pd.ExcelWriter(excel_filename, engine='xlsxwriter')

    df.to_excel(writer, sheet_name='Sheet1', index=False, freeze_panes=(1, 0))
    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    wrap = workbook.add_format({'text_wrap': True, 'valign': 'top'})

    # Set column widths
    base_col_width = 20
    col_width_scale_factors = {
        'conversation_id': 0.4,
        'messageId': 0.45,
        'role': 0.4,
        'message': 3.5,
        # 'visited_agents': 0.9,
        'location_details': 1.05,
        'expected_location_details': 1.05,
    }

    for col in df.columns:
        col_idx = df.columns.get_loc(col)
        worksheet.set_column(col_idx, col_idx, base_col_width, wrap)
        if col in col_width_scale_factors.keys():
            scale_factor = col_width_scale_factors[col]
            worksheet.set_column(col_idx, col_idx, base_col_width * scale_factor, wrap)

    # Visually separate convos with borders by adding top border to rows where MessageId=1
    border = workbook.add_format({'top': 5})
    worksheet.conditional_format('A1:Z10000', {'type': 'formula',
                                               'criteria': '$B1=1',
                                               'format': border})
    writer.close()
