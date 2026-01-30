import pandas as pd
import re
import ast
import json

def process_messages(c_df, t_df):

    ####
    # Merge consent into transcript
    ###

    combined_df = pd.merge(c_df, t_df, on='user', how='inner')

    print("Consent Data Combined into DataFrame.")
    # display(combined_df.head())

    ####
    # Split up question column
    ###

    # Define the regex pattern to capture the components
    pattern = r"(.+) - Assignment (\d+) Question (\d+) - (.+)"

    # Apply the regex to the 'question' column and create new columns
    combined_df[['Course', 'lab_number', 'question_number', 'question_text']] = \
        combined_df['question'].str.extract(pattern)

    # Convert lab_number and question_number to numeric types
    combined_df['lab_number'] = pd.to_numeric(combined_df['lab_number'])
    combined_df['question_number'] = pd.to_numeric(combined_df['question_number'])

    # Format lab_number and question_number to add leading zeros if single digit
    combined_df['lab_number'] = combined_df['lab_number'].astype(int).astype(str).str.zfill(2)
    combined_df['question_number'] = combined_df['question_number'].astype(int).astype(str).str.zfill(2)

    # Replace the 'question' column with the new formatted string
    combined_df['question'] = 'Lab ' + combined_df['lab_number'] + '-Q' + combined_df['question_number']

    print(' Question Data parsed and updated.')

    ####
    # Convert the JSON format to lists of dicts
    ###

    # Function to parse message strings into list of dictionaries
    def parse_messages(message_string):
        if pd.isna(message_string) or message_string == '[]':
            return []
        try:
            return json.loads(message_string)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(message_string)
            except (ValueError, SyntaxError):
                return [] # Return empty list if parsing fails

    # Apply the parsing function to the 'all_messages' column
    combined_df['all_messages'] = combined_df['all_messages'].apply(parse_messages)

    # Count message objects in 'all_messages' and add to 'interactions' column
    combined_df['interactions'] = combined_df['all_messages'].apply(len)

    import json
    combined_df = combined_df[combined_df['all_messages'].apply(lambda x: len(x) > 0)]

    print("Combined DataFrame with split question columns and interactions:")
    # display(combined_df.head())
    return combined_df