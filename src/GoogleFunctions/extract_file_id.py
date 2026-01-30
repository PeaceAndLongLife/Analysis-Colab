# @title ## Extract File ID {"form-width":"20%"}
# @markdown This Python function is designed to extract the file ID from a Google Drive shared link.



def extract_file_id(shared_link):
    import re
    """
    Extracts the Google Drive file ID from a shared link.

    Args:
        shared_link (str): The Google Drive shared link.

    Returns:
        str: The extracted file ID, or None if not found.
    """
    # Pattern 1: https://drive.google.com/file/d/FILE_ID/view
    # Pattern 2: https://drive.google.com/open?id=FILE_ID
    # Pattern 3: https://docs.google.com/spreadsheets/d/FILE_ID/edit (and similar for other doc types)
    # Pattern 4: https://drive.google.com/drive/folders/FOLDER_ID
    patterns = [
        r"https:\/\/drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)",
        r"https:\/\/drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)",
        r"https:\/\/docs\.google\.com\/(?:spreadsheets|document|presentation)\/d\/([a-zA-Z0-9_-]+)",
        r"https:\/\/drive\.google\.com\/drive\/folders\/([a-zA-Z0-9_-]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, shared_link)
        if match:
            return match.group(1)

    return None

print("The 'extract_file_id' function has been defined.")
