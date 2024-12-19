from pydantic import BaseModel
from typing import Optional,List

class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: str 
    capabilities: dict
    
class ProjectResponse(BaseModel):
    id: str
    name: Optional[str] = None 
    description: Optional[str] = None
    state: Optional[str] = None  
    last_update_time: Optional[str] = None 
    status_code: int = 200
    
class ProjectListResponse(BaseModel):
    count: int
    value: List[ProjectResponse]

class WorkItemModel(BaseModel):
    id: int
    title: str
    state: str
