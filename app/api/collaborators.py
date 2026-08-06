from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.collaboration import User, ProjectMember, Role, Project
from app.services.activity_logger import log_activity

router = APIRouter(tags=["Collaborators"])

class AddMemberRequest(BaseModel):
    email: str
    role: str  # As per user request, treat role as a string

@router.post("/projects/{project_id}/members")
async def add_project_member(
    project_id: int,
    request: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if project exists
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the user by email
    result = await db.execute(select(User).where(User.email == request.email))
    new_user = result.scalars().first()
    if not new_user:
        raise HTTPException(status_code=404, detail="User not found with this email")
        
    # Get or create Role based on string
    result = await db.execute(select(Role).where(Role.name == request.role))
    role = result.scalars().first()
    if not role:
        role = Role(name=request.role, description=f"Auto-created role: {request.role}")
        db.add(role)
        await db.commit()
        await db.refresh(role)

    # Check if already a member
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, 
            ProjectMember.user_id == new_user.user_id
        )
    )
    existing_member = result.scalars().first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    # Add member
    member = ProjectMember(
        project_id=project_id,
        user_id=new_user.user_id,
        role_id=role.role_id
    )
    db.add(member)
    await db.commit()
    
    # Log Activity
    await log_activity(
        db=db, project_id=project_id, user_id=current_user.user_id, 
        action="Added Member", entity_type="user", entity_id=new_user.user_id,
        metadata={"role": role.name}
    )
    
    return {"message": "Member added successfully", "member_id": member.member_id}

@router.get("/projects/{project_id}/members")
async def get_project_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch members with users and roles
    result = await db.execute(
        select(ProjectMember, User.full_name, User.email, Role.name.label("role_name"))
        .join(User, ProjectMember.user_id == User.user_id)
        .join(Role, ProjectMember.role_id == Role.role_id)
        .where(ProjectMember.project_id == project_id)
    )
    
    members = []
    for member, name, email, role_name in result.all():
        members.append({
            "member_id": member.member_id,
            "user_id": member.user_id,
            "name": name,
            "email": email,
            "role": role_name,
            "joined_at": member.joined_at,
            "is_active": member.is_active
        })
        
    return members
