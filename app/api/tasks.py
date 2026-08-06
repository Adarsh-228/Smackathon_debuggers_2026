from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.collaboration import User, Task, Project
from app.models.workflow import Notification
from app.services.activity_logger import log_activity

router = APIRouter(tags=["Tasks"])

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: int
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None
    document_id: Optional[int] = None

class UpdateTaskRequest(BaseModel):
    status: str

@router.post("/projects/{project_id}/tasks")
async def create_task(
    project_id: int,
    request: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = Task(
        project_id=project_id,
        title=request.title,
        description=request.description,
        assigned_by=current_user.user_id,
        assigned_to=request.assigned_to,
        priority=request.priority,
        due_date=request.due_date,
        document_id=request.document_id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Trigger In-App Notification for assignee
    notification = Notification(
        user_id=request.assigned_to,
        title="New Task Assigned",
        body=f"You have been assigned a new task: '{task.title}'",
        link=f"/projects/{project_id}/tasks/{task.task_id}"
    )
    db.add(notification)
    
    # Log Activity
    await log_activity(
        db=db, project_id=project_id, user_id=current_user.user_id, 
        action="Created Task", entity_type="task", entity_id=task.task_id,
        metadata={"assigned_to": request.assigned_to, "title": task.title}
    )
    await db.commit()
    
    return {"message": "Task created successfully", "task_id": task.task_id}

@router.get("/projects/{project_id}/tasks")
async def get_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = result.scalars().all()
    return tasks

@router.patch("/tasks/{task_id}")
async def update_task_status(
    task_id: int,
    request: UpdateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.status = request.status
    await db.commit()
    
    await log_activity(
        db=db, project_id=task.project_id, user_id=current_user.user_id, 
        action=f"Updated Task Status to {request.status}", entity_type="task", entity_id=task.task_id
    )
    
    return {"message": "Task updated successfully", "status": task.status}
