from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.collaboration import User, Comment
from app.models.document import DocumentVersion
from app.services.activity_logger import log_activity

router = APIRouter(tags=["Comments"])

class CreateCommentRequest(BaseModel):
    text: str
    block_id: Optional[int] = None
    parent_comment_id: Optional[int] = None

@router.post("/documents/{version_id}/comments")
async def add_comment(
    version_id: int,
    request: CreateCommentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get document_id from version to store it (and project_id for logging)
    result = await db.execute(select(DocumentVersion).where(DocumentVersion.version_id == version_id))
    version = result.scalars().first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    comment = Comment(
        document_id=version.document_id,
        version_id=version_id,
        block_id=request.block_id,
        author_id=current_user.user_id,
        parent_comment_id=request.parent_comment_id,
        text=request.text
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Ideally we'd get project_id from document, but assuming Document model has project_id:
    # await log_activity(db, project_id=document.project_id, user_id=current_user.user_id, action="Added Comment", entity_type="comment", entity_id=comment.comment_id)
    
    return {"message": "Comment added successfully", "comment_id": comment.comment_id}

@router.get("/documents/{version_id}/comments")
async def get_comments(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Comment).where(Comment.version_id == version_id))
    comments = result.scalars().all()
    return comments

@router.patch("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import datetime
    
    result = await db.execute(select(Comment).where(Comment.comment_id == comment_id))
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    comment.status = "resolved"
    comment.resolved_by = current_user.user_id
    comment.resolved_at = datetime.datetime.utcnow()
    
    await db.commit()
    return {"message": "Comment resolved successfully"}
