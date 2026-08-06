from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.collaboration import Project, Organization, User
from app.models.workflow import Activity
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify organization exists
    result = await db.execute(select(Organization).where(Organization.organization_id == project_in.organization_id))
    if not result.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    db_project = Project(
        **project_in.model_dump(),
        created_by=current_user.user_id,
        lead_user_id=current_user.user_id # Defaulting lead to creator for now
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

@router.get("/", response_model=List[ProjectResponse])
async def read_projects(
    skip: int = 0, limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Project).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{project_id}", response_model=ProjectResponse)
async def read_project(
    project_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

@router.get("/{project_id}/activities")
async def get_project_activities(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Activity, User.full_name)
        .join(User, Activity.user_id == User.user_id)
        .where(Activity.project_id == project_id)
        .order_by(Activity.created_at.desc())
        .limit(100)
    )
    
    activities = []
    for activity, user_name in result.all():
        activities.append({
            "activity_id": activity.activity_id,
            "user_id": activity.user_id,
            "user_name": user_name,
            "action": activity.action,
            "entity_type": activity.entity_type,
            "entity_id": activity.entity_id,
            "metadata": activity.metadata_json,
            "timestamp": activity.created_at
        })
        
    return activities
