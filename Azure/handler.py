import base64
import json
import os
import httpx
from dotenv import load_dotenv # type: ignore
load_dotenv()

API_URL = os.getenv('API_URL')

def header(token: str) -> dict[str, str]:
    token_base64 = base64.b64encode(f":{token}".encode()).decode()
    headers = {
        'Authorization': f'Basic {token_base64}',
        'Content-Type': 'application/json',
    }
    
    return headers

def send_discord_notification(message: str, webhook:str) -> None:
    payload = {
        "content": message
    }
    try:
        response = httpx.post(webhook, json=payload)
        response.raise_for_status()  
    except httpx.RequestError as e:
        print(f"Failed to send notification: {e}")

def lambda_handler(event, context) -> dict:
    """AWS Lambda function to process messages from SQS."""
    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            command = message_body.get('command')
            data = message_body.get('data')
            token = message_body.get('token')
            webhook = message_body.get('webhook')

            if not command or not data or not token:
                raise ValueError(f"Missing required fields in message: {message_body}")

            if command == 'create_project':
                create_project(data, token, webhook)
            elif command == 'delete_project':
                delete_project(data, token, webhook)
            elif command == 'update_item':
                update_item(data, token, webhook)
            elif command == 'create_item':
                create_item(data, token, webhook)
            elif command == 'delete_item':
                delete_item(data, token, webhook)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON decode error: {e}") 

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully!')
    }


def create_project(data: dict, token: str, webhook:str) -> None:
    """Create a new project in Azure DevOps."""
    headers = header(token)
    project_name = data.get('name') 
    description = data.get('description')
    if project_name == "A1":
        raise Exception("Intentional failure to trigger DLQ for testing.")
    
    url = f'{API_URL}/_apis/projects?api-version=7.2-preview.4'
    
    payload = {
        "name": project_name,
        "description": description,
        "visibility": "private",
        "capabilities": {
            "versioncontrol": {
                "sourceControlType": "Git"
            },
            "processTemplate": {
                "templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45"  
            }
        }
    }

    response = httpx.post(url, headers=headers, json=payload)
    if response.status_code in (200, 201, 202):
        send_discord_notification("Operation result: Create project Successfully", webhook)
    else:
        send_discord_notification("Operation result: Create project Failed", webhook)

    
 
def delete_project(data: dict, token: str, webhook:str) -> None:
    """Delete a project in Azure DevOps."""
    headers = header(token)
    project_id = data.get('project_id')
    url = f'{API_URL}/_apis/projects/{project_id}?api-version=7.2-preview.4'
    response = httpx.delete(url, headers=headers)
    if response.status_code in (200, 201, 202):
        send_discord_notification("Operation result: delete project Successfully", webhook)
    else:
        send_discord_notification("Operation result: delete project Failed", webhook)
    


    
def create_item(data: dict, token: str, webhook:str) -> None:
    """Create a new work item in Azure DevOps."""
    headers = header(token)
    project = data.get('project_id')
    work_item_type = data.get('work_item_type')
    title = data.get('title')

    url = f'{API_URL}/{project}/_apis/wit/workitems/${work_item_type}?api-version=7.2-preview.3'
    
    payload = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title
        },
    ]

    response = httpx.post(url, headers=headers, json=payload)
    if response.status_code in (200, 201, 202):
        send_discord_notification("Operation result: create item Successfully", webhook)
    else:
        send_discord_notification("Operation result: create item Failed", webhook)
    
def update_item(data: dict, token: str, webhook:str) -> None:
    """Update a work item in Azure DevOps."""
    headers = header(token)
    project = data.get('project_id')
    work_item_id = data.get('work_item_id')
    title = data.get('title')

    url = f'{API_URL}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.2-preview.3'
    

    payload = [
        {
            "op": "replace",
            "path": "/fields/System.Title",
            "value": title
        },
    ]

    response = httpx.patch(url, headers=headers, json=payload)
    if response.status_code in (200, 201, 202):
        send_discord_notification("Operation result: update item Successfully", webhook)
    else:
        send_discord_notification("Operation result: update item Failed", webhook)
    
def delete_item(data: dict, token: str, webhook:str) -> None:
    """Delete a work item in Azure DevOps."""
    headers = header(token)
    project = data.get('project_id')
    work_item_id = data.get('work_item_id')

    url = f'{API_URL}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.2-preview.3'

    response = httpx.delete(url, headers=headers)
    if response.status_code in (200, 201, 202):
        send_discord_notification("Operation result: delete item Successfully", webhook)
    else:
        send_discord_notification("Operation result: delete item Failed", webhook)

