from GoogleFunctions import GoogleDocumentManager
from IPython.display import display

def read_csv_from_id(
        SERVICE_ACCOUNT_FILE, 
        link_id,
        show = True
):
    GDM = GoogleDocumentManager(SERVICE_ACCOUNT_FILE)

    print(f"Reading in csv file. id={link_id}")
    df = GDM.read_csv(
        document_id=link_id,
        file_type = 'csv',
        )
    if show:
        display(df)
    return df