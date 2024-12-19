import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build  # type: ignore
from datetime import datetime
from django.conf import settings

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheets_service():
    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    return service

def append_to_google_sheet(spreadsheet_id, range_name, values):
    service = get_google_sheets_service()
    body = {
        'values': values
    }
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

def log_payment(client_name, amount, job_id):
     
    values = [[
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  
        client_name,
        'Payment',
        amount,
        job_id
    ]]
    append_to_google_sheet(settings.SPREADSHEET_ID, settings.RANGE_NAME, values)

def log_deposit(client_name, amount):
     
    values = [[
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  
        client_name,
        'Deposit',
        amount,
        ''
    ]]
    append_to_google_sheet(settings.SPREADSHEET_ID, settings.RANGE_NAME, values)
  