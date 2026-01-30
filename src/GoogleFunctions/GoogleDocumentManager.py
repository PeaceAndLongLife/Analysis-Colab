import os
import io
import re
import pandas as pd # Assuming pandas is used for CSVs
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

### Google Docs client manager
class GoogleDocumentManager:
    def __init__(self, service_account_file_path):
        self.creds = service_account.Credentials.from_service_account_file(
            service_account_file_path,
            scopes=['https://www.googleapis.com/auth/drive', 
                    'https://www.googleapis.com/auth/documents', 
                    'https://www.googleapis.com/auth/spreadsheets']
        )
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        print("Google Drive API service built successfully.")
    
    ## Get parent folder info for a Google Spreadsheet
    def get_file_parent_info(self, file_id):
        try:
            file = self.drive_service.files().get(
                fileId=file_id,
                fields="id,name,parents,mimeType",
                supportsAllDrives=True

            ).execute()
            parent_ids = file.get("parents", [])

            parents = []
            for parent_id in parent_ids:
                parent = self.drive_service.files().get(
                    fileId=parent_id,
                    fields="id,name,mimeType",
                    supportsAllDrives=True,

                ).execute()
                parents.append(parent)

            return {
                "fileId": file.get("id"),
                "fileName": file.get("name"),
                "parents": parents
            }
        except HttpError as error:
            errorStr = f"An HTTP error occurred while fetching parent info: {error}"
            return errorStr
        except Exception as e:
            errorStr =f"An unexpected error occurred while fetching parent info: {e}"
            return errorStr

    ## Copy a Google Drive file (Docs, Sheets, Slides, or any Drive file) and rename it
    def copy_file(self, file_id, new_name, parent_folder_id=None):
        try:
            body = {
                "name": new_name
            }
                        # Optionally set a new parent folder
            if parent_folder_id:
                body["parents"] = [parent_folder_id]

            copied_file = self.drive_service.files().copy(
                fileId=file_id,
                body=body,
                supportsAllDrives=True
            ).execute()

            return copied_file.get("id")

        except HttpError as error:
            errorStr = f"An HTTP error occurred while copying file: {error}"
            return errorStr
        except Exception as e:
            errorStr = f"An unexpected error occurred while copying file: {e}"
            return errorStr


    ## Read CSV file from Google Drive        
    def read_csv(self, document_id, file_type='csv'):
        # For simplicity, assuming a common use case like reading CSV
        # This method can be expanded to handle different mime types or Google Doc formats
        try:

            # Download the file content
            request = self.drive_service.files().get_media(fileId=document_id)
            file_content = request.execute()

            # Read file into DataFrame based on file_type
            if file_type.lower() == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            elif file_type.lower() == 'xlsx':
                df = pd.read_excel(io.BytesIO(file_content))
                print(df.head())
            return df

        # Raise errors is necessary
        except HttpError as error:
            print(f"An HTTP error occurred: {error}")
            return None
        except FileNotFoundError:
            print(f"Error: Service account key file not found at '{self.service_account_file}'")
            print("Please ensure the path to your service account key is correct.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    ## Read google docs file from Drive
    def read_document_content(self, document_id):
        # Reads content of a Google Doc (not just export, but structured content)
        doc = self.docs_service.documents().get(documentId=document_id).execute()
        return doc

    ## Read google sheet file from Drive
    def read_spreadsheet_content(self, spreadsheet_id, range_name='Sheet1'):
        # Reads content of a Google Sheet
        result = self.sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id, 
            fields="spreadsheetId,properties,spreadsheetUrl"
            ).execute()
        properties = result.get('properties', {})
        return properties

    ## Upload dataframe as CSV to Google Drive
    def upload_dataframe_to_drive(self, df_to_upload, filename, folder_id):
        if folder_id == 'YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE':
            print(f"\nWarning: Please replace 'YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE' with your actual Google Drive Folder ID to save '{filename}'.")
            return None

        try:
            csv_buffer = io.StringIO()
            df_to_upload.to_csv(csv_buffer, index=True)
            csv_content = csv_buffer.getvalue()

            # Wrap the CSV content in a MediaIoBaseUpload object
            media_body = MediaIoBaseUpload(io.BytesIO(csv_content.encode('utf-8')),
                                           mimetype='text/csv',
                                           resumable=True)

            file_metadata = {
                'name': filename,
                'parents': [folder_id],
                'mimeType': 'text/csv'
            }

            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media_body, # Use the wrapped media_body
                fields='id',
                supportsAllDrives=True,
            ).execute()

            print(f"Successfully uploaded '{filename}' to Google Drive (File ID: {file.get('id')}).")
            return file.get('id')

        except FileNotFoundError:
            print(f"Error: Service account key file not found at '{self.service_account_file}'")
            print("Please ensure the path to your service account key is correct.")
            return None
        except HttpError as error:
            print(f"An HTTP error occurred during upload: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during upload: {e}")
            return None
    
    def export_md(self, markdown_text, filename, folder_id):
        if not filename.lower().endswith(".md"):
            filename = f"{filename}.md"
        try:
            media_body = MediaIoBaseUpload(
            io.BytesIO(markdown_text.encode("utf-8")),
            mimetype="text/markdown",
            resumable=True
            )
            file_metadata = {
            "name": filename,
            "parents": [folder_id],
            "mimeType": "text/markdown"
            }
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media_body,
                fields="id",
                supportsAllDrives=True
            ).execute()

            print(
            f"Successfully uploaded '{filename}' to Google Drive "
            f"(File ID: {file.get('id')})."
            )
            return file.get("id")
        except HttpError as error:
            print(f"An HTTP error occurred during Markdown upload: {error}")
            return None
        
        except Exception as e:
            print(f"An unexpected error occurred during Markdown upload: {e}")
            return None