# @title explode_json_messages function
import pandas as pd

def explode_json_messages(df):
  df = df.explode('all_messages').reset_index(drop=True)

  # Extract details from the 'all_messages' dictionary
  # First, ensure that 'all_messages' contains dictionaries, if not, handle it
  df['all_messages'] = df['all_messages'].apply(lambda x: x if isinstance(x, dict) else {})

  messages_df = pd.json_normalize(df['all_messages'])

  # Rename columns from messages_df to avoid conflicts and make them more descriptive
  messages_df = messages_df.rename(columns={'role': 'message_role', 'content': 'message_content', 'time': 'message_time'})

  # Drop the original 'all_messages' column before concatenating
  df = df.drop(columns=['all_messages'])

  # Concatenate the new columns with the exploded_df
  # It's crucial that both dataframes have the same index for a correct join/concat
  df = pd.concat([df, messages_df], axis=1)

  return df