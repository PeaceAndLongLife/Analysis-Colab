# @title convert_utc_to_la function
from datetime import datetime
import pytz

def convert_utc_to_la(iso_str):
    # 1. Parse the string
    dt = datetime.fromisoformat(iso_str)

    # 2. Check if it is UTC (+00:00)
    # This ensures we only convert the ones that need it
    if dt.utcoffset().total_seconds() == 0:
        la_tz = pytz.timezone('America/Los_Angeles')
        # .astimezone() performs the clock-shift math
        return dt.astimezone(la_tz)

    # If it's already in another timezone, return as is
    return dt

# Example: 8:00 PM UTC (20:00)
# In LA (Winter), this should be 12:00 PM (noon)
print(convert_utc_to_la("2026-01-28T20:00:00+00:00"))
# Output: 2026-01-28 12:00:00-08:00