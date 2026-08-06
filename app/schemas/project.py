from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[date] = None
    status: str = "active"
    current_stage: Optional[str] = None

class ProjectCreate(ProjectBase):
    organization_id: int

class ProjectUpdate(ProjectBase):
    title: Optional[str] = None
    organization_id: Optional[int] = None

class ProjectResponse(ProjectBase):
    project_id: int
    organization_id: int
    lead_user_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
