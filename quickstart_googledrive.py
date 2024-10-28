from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import io
import os
import pickle
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10792'

# 需要增加CONTCAR，CIF等文件夹对应的代码
# 文件代码对应字典
# dir_dict = {
#     "pdfs": "11GcpDma5EpTkWW5Ip7BDislEQ-4XW7MF",
#     "total_excel": "1cF0RuafYEghVuejjz_VZC1yBB6Gbfb4N",
#     "user": "1BvHhy3k_9oelJ1RT9nRuB3s_XWGxq041",
#     "pdfs_thermocatalysis": "1bqKx8U0yydCihdpyRDT3PFmZtoAHXLre",
#     "pdfs_photocatalysis": "1yZycUWaO3T9cTj2OF7Mje-qScBvSUrMe",
#     "total_pickle_thermocatalysis": "14jcGT3YDNSziV27fP7IORSOuPazuGeEf",
#     "total_pickle_photocatalysis":"1vjw8JYJMPNX4jkaBFDfESCBy6DlR45qj"
#     }

dir_dict = {
    "pdfs": "1dv8uuilYHnIz_Aa1phQDjOyz3gekeCH4",
    "total_excel": "1yj9qDe2CEElYk4GEvaTOR4qx7myk0TDq",
    "user": "1HoybEESYRvuEXlYYULBX8zqMR9wMtC4N",
    "pdfs_thermocatalysis": "1edcoBJnw3SIlCkkDp_Sjn0OcyItcRjx7",
    "pdfs_photocatalysis": "1jCvYrbuS0OXfl1Qu12Gt4HBNZ4TJE-Or",
    "total_pickle_thermocatalysis": "1LzN2mQxKdptEqMNXIbFccHcneGpQKUx7",
    "total_pickle_photocatalysis": "1tu1GxxCKZjmgEGI1p8qxjHyzqMYEfZbM",
    "computational_data": "13R0jhHh39YBUSTf1-4Sxoc59CGT2Hk8C",
    "CIF": "1--gBoXJxbZaBgB2Q1svZpS3LHM9ARNpA",
    "CONTCAR": "1-147G62VzfWObnprYgA_swHmrim3mhN8",
    "INCAR": "1-62JuENWCnmtKBkJa2BEy23F5m7iHgFX",
    "KPOINTS": "1-CJG2VeeKejkhnHG2I9qRctUgJ-fexvl",
}
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def delete_files_in_folder_googledrive(folder_id, service):
    # 查询文件夹下的所有文件
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
    files = results.get("files", [])

    # 遍历文件列表
    for file in files:
        file_id = file["id"]
        file_name = file["name"]

        # 删除文件
        service.files().delete(fileId=file_id).execute()
        print(f"Deleted file: {file_name}")
 
 
def init_drive_client():
    # creds = Credentials.from_service_account_file('./streamlitren-e6009aae6aa6.json')
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # if os.path.exists("token.json"):
    #     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if os.path.exists("./authentic_file/token.pickle"):
        with open("./authentic_file/token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
        else:
          flow = InstalledAppFlow.from_client_secrets_file(
              "./authentic_file/credentials.json", SCOPES
          )
          creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    # with open("token.json", "w") as token:
    #     token.write(creds.to_json())
    with open('./authentic_file/token.pickle', 'wb') as token:
        pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


# Function to upload files to Google Drive
def st_upload_file_to_drive(file, folder_id, client):
    # Search for existing file with the same name in the specified folder
    query = f"name='{file.name}' and '{folder_id}' in parents and mimeType='application/pdf'"
    existing_files = client.files().list(q=query, fields="files(id)").execute().get('files', [])

    file_metadata = {'name': file.name, 'parents': [folder_id]}
    media_body = MediaIoBaseUpload(file, mimetype='application/pdf')
    # If file exists, update it; otherwise, create a new file
    if existing_files:
        file_id = existing_files[0]['id']  # Assuming there is only one file with this name
        updated_file = client.files().update(fileId=file_id, media_body=media_body).execute()
        return updated_file['id']
    else:
        new_file = client.files().create(body=file_metadata, media_body=media_body, fields='id').execute()
        return new_file['id']


# Function to list files in Google Drive
def list_files_in_drive(client):
    results = client.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items


def upload_file_to_drive(filename, filepath, mimetype, folder_id, drive_service):
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(filepath, mimetype=mimetype)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')
    

def list_files_in_folder(folder_id, drive_service=init_drive_client()):
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items
    

# 上传与更新
def upload_or_replace_file(filename, filepath, mimetype, folder_id, drive_service=init_drive_client()):
    # Search for the file within the specified folder
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    response = drive_service.files().list(q=query, 
                                          spaces='drive', 
                                          fields='files(id, name)').execute()
    files = response.get('files', [])
    
    media_body = MediaIoBaseUpload(io.FileIO(filepath, 'rb'), mimetype=mimetype)

    if files:
        # File exists, update it
        file_id = files[0]['id']
        updated_file = drive_service.files().update(fileId=file_id, media_body=media_body).execute()
        return updated_file['id']
    else:
        # File does not exist, create it
        file_metadata = {'name': filename, 'parents': [folder_id]}
        file = drive_service.files().create(body=file_metadata, media_body=media_body, fields='id').execute()
        return file['id']


def upload_to_gdrive(service, file_path, folder_id):
    """Upload a file to a specific folder in Google Drive."""
    file_name = os.path.basename(file_path)
    # 创建一个文件的 metadata
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]  # 指定父文件夹 ID
    }

    # 使用 MediaFileUpload 处理要上传的文件
    media = MediaFileUpload(file_path, resumable=True)

    # 执行上传操作
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"文件 {file_name} 上传成功，文件 ID: {file.get('id')}")


def upload_or_replace_file_by_file(filename, file, mimetype, folder_id, drive_service=init_drive_client()):
    # Search for the file within the specified folder
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    response = drive_service.files().list(q=query,
                                          spaces='drive',
                                          fields='files(id, name)').execute()
    files = response.get('files', [])

    media_body = MediaIoBaseUpload(file, mimetype=mimetype)

    if files:
        # File exists, update it
        file_id = files[0]['id']
        updated_file = drive_service.files().update(fileId=file_id, media_body=media_body).execute()
        return updated_file['id']
    else:
        # File does not exist, create it
        file_metadata = {'name': filename, 'parents': [folder_id]}
        file = drive_service.files().create(body=file_metadata, media_body=media_body, fields='id').execute()
        return file['id']


def create_or_get_subfolder_id(service, subfolder_name, parent_folder_id):
    """在 Google Drive 中创建或获取子文件夹的 folder_id."""
    query = f"'{parent_folder_id}' in parents and name='{subfolder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])

    if items:
        # 子文件夹已存在，返回其 ID
        return items[0]['id']
    else:
        # 创建新子文件夹
        file_metadata = {
            'name': subfolder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')



# 下载文件
def file_from_gdrive(folder_id, file_name, service, local_path):
    query = f"'{folder_id}' in parents and name='{file_name}'"
    response = service.files().list(q=query, spaces='drive',
                                    fields='nextPageToken, files(id, name)', pageToken=None).execute()
    for file in response.get('files', []):
        request = service.files().get_media(fileId=file['id'])
        fh = io.FileIO(local_path, mode='wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.close()
        return local_path


def download_file(file_id, service):
    
    request = service.files().get_media(fileId=file_id)
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read()


def download_folder_contents(folder_id, local_folder_path, drive_service = init_drive_client()):
    # Get list of all files in the folder
    query = f"'{folder_id}' in parents and trashed=false"
    response = drive_service.files().list(q=query, fields="files(id, name)").execute()
    print(response)
    files = response.get('files', [])

    # Ensure the local folder exists
    if not os.path.exists(local_folder_path):
        os.makedirs(local_folder_path)

    # Download each file
    for file in files:
        file_id = file['id']
        file_name = file['name']
        request = drive_service.files().get_media(fileId=file_id)
        file_path = os.path.join(local_folder_path, file_name)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        

if __name__ == "__main__":
    cwd = os.getcwd()
    drive_client = init_drive_client()
    excel_file_name = os.path.join(cwd, "total_excel", 'ElectroCatalyst_Database_240602.xlsx')
    yaml_file_path = os.path.join(cwd, "user.yaml")
    #upload_file_to_drive(filename, os.path.join(cwd, filename), 'application/xlsx', dir_dict["excels"], drive_client)
    upload_or_replace_file("user.yaml", yaml_file_path, 'application/x-yaml', dir_dict["user"], drive_client)
    #file = file_from_gdrive(dir_dict["excels"], filename, drive_client)
    #df = pd.read_excel(file, sheet_name="ORR")
    #print(df["Formula"][0])
    #download_folder_contents(dir_dict["total_excel"], os.path.join(cwd, "total_excel"), drive_client)
    #file_from_gdrive(dir_dict["user"], "user.yaml", drive_client, yaml_file_path)
        
    
