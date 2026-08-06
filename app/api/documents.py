from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.collaboration import User
from app.models.document import Document, DocumentVersion
from app.services.document_parser import parse_document_blocks
from app.services.reconciliation_engine import generate_trust_report

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/reconcile")
async def reconcile_documents(
    files: List[UploadFile] = File(...),
    intended_corrections: str = Form(...), # JSON string array of corrections
    project_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts multiple manuscript files (in order) and a list of intended corrections.
    Processes them through the parser and reconciliation engine.
    Returns the Trust Report.
    """
    if len(files) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two files are required for reconciliation."
        )
        
    try:
        corrections_list = json.loads(intended_corrections)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="intended_corrections must be a valid JSON array of strings."
        )

    version_blocks = []
    filenames = []
    
    for file in files:
        filenames.append(file.filename)
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        file_bytes = await file.read()
        
        try:
            # Parse semantic blocks
            blocks = parse_document_blocks(file_bytes, ext)
            print(f"Extracted {len(blocks)} blocks from {file.filename}")
            version_blocks.append(blocks)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to process {file.filename}: {str(e)}"
            )
            
    # Generate the Trust Report
    try:
        report = generate_trust_report(filenames, version_blocks, corrections_list)
        
        # Save to database if part of a project
        if project_id:
            db_doc = Document(
                project_id=project_id,
                title=f"Analysis: {filenames[0]} to {filenames[-1]}",
                description="Auto-generated document timeline from reconciliation",
                created_by=current_user.user_id
            )
            db.add(db_doc)
            await db.flush()
            
            for i, filename in enumerate(filenames):
                db_ver = DocumentVersion(
                    document_id=db_doc.document_id,
                    version_label=f"v{i+1}",
                    uploaded_by=current_user.user_id,
                    storage_path=filename, # Mapped to original filename for prototype
                    file_size=0
                )
                db.add(db_ver)
            await db.commit()

        return {"report": report}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation engine failed: {str(e)}"
        )

@router.get("/projects/{project_id}/documents")
async def get_project_documents(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.versions))
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    
    output = []
    for doc in docs:
        versions = [{"version_label": v.version_label, "filename": v.storage_path, "upload_time": v.upload_time} for v in doc.versions]
        output.append({
            "document_id": doc.document_id,
            "title": doc.title,
            "description": doc.description,
            "created_at": doc.created_at,
            "versions": versions
        })
    return {"documents": output}
