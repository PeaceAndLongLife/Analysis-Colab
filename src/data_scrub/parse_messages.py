import json
import ast
import pandas as pd
def parse_messages(message_string):
    print(f"message string is: _{message_string}_")

    if pd.isna(message_string) or message_string == '[]' or message_string == " ":
        return []
    try:
        return json.loads(message_string)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(message_string)
        except (ValueError, SyntaxError):
            return [] # Return empty list if parsing fails