# drive_utils.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = './drive.json' 
FOLDER_ID = '1yfrjt3p7V6AIovwxMimUUBCktb2mk5BU'
DOWNLOAD_DIR = './pdfs'

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=credentials)

def list_pdfs_in_folder(service):
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false",
        fields="files(id, name)").execute()
    return results.get('files', [])

def download_file(service, file_id, filename):
    from googleapiclient.http import MediaIoBaseDownload
    import io

    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        print(f"⏩ Skipping already downloaded: {filename}")
        return False

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filepath, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    print(f"✅ Downloaded: {filename}")
    return True
