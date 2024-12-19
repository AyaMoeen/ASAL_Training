import httpx
from Azure.req_res import ProjectResponse, ProjectListResponse 
from Azure.handler import header, API_URL


def list_projects(token: str) -> ProjectListResponse:
    headers = header(token)
    response = httpx.get(f'{API_URL}/_apis/projects?api-version=7.2-preview.4', headers=headers)
    
    if response.status_code in (200, 201):
        return ProjectListResponse.model_validate(response.json())
    else:
        raise Exception(f"Error listing projects: {response.status_code} - {response.text}")


def get_project(token: str, project_id: str) -> ProjectResponse:
    headers = header(token)
    response = httpx.get(f'{API_URL}/_apis/projects/{project_id}?api-version=7.2-preview.4', headers=headers)
    
    if response.status_code in (200, 201):
        return ProjectResponse.model_validate(response.json())
    elif response.status_code == 202:
        return ProjectResponse(
            id=response.json().get('id'), 
            status_code= response.status_code, 
            name=response.json().get('name')
        ) 
    else:
        raise Exception(f"Error fetching project: {response.status_code} - {response.text}")
    
def list_work_items_azure(token: str, project: str, ids: str) -> dict:
    headers = header(token)
    response = httpx.get(
        f'{API_URL}/{project}/_apis/wit/workitems?ids={ids}&api-version=7.2-preview.3',
        headers=headers
    )

    if response.status_code in (200, 201):
        return response.json() 
    else:
        raise Exception(f"Error listing work items: {response.status_code}")
    
def get_work_item_azure(token: str, project: str, work_item_id: int) -> dict:
    headers = header(token)
    response = httpx.get(
        f'{API_URL}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.2-preview.3',
        headers=headers
    )
    
    if response.status_code in (200, 201):
        return response.json()
    else:
        raise Exception(f"Error getting work item: {response.status_code}")
 
