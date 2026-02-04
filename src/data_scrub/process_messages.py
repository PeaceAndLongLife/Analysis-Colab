import pandas as pd
from data_scrub import parse_messages
import json

def process_messages(
        c_df, 
        t_df,
        pattern_col = 'question',
        pattern = r"(.+) - Assignment (\d+) Question (\d+) - (.+)", # regex pattern to capture the components
        new_columns = ['Course', 'lab_number', 'question_number', 'question_text'],
        new_numeric_columns = ['lab_number', 'question_number']
        ):

    ####
    # Merge consent into transcript
    ###

    combined_df = pd.merge(c_df, t_df, on='user', how='inner')

    print("Consent Data Combined into DataFrame.")
    # display(combined_df.head())

    ####
    # Split up question column
    ###    

    # Apply the regex to the 'question' column and create new columns
    combined_df[new_columns] = \
        combined_df[pattern_col].str.extract(pattern)

    # Convert numeric columns to numeric types and add leading zeros
    for num_col in new_numeric_columns:
        combined_df[num_col] = pd.to_numeric(combined_df[num_col])
        combined_df[num_col] = combined_df[num_col].astype(int).astype(str).str.zfill(2)

    # Replace the 'question' column with the new formatted string
    combined_df['question'] = 'Lab ' + combined_df['lab_number'] + '-Q' + combined_df['question_number']

    print(' Question Data parsed and updated.')
    
    return combined_df

 