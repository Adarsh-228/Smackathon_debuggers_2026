from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import uuid

from app.core.database import get_db
from app.services.document_parser import parse_document_blocks
from app.services.reconciliation_engine import generate_trust_report

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/reconcile")
async def reconcile_documents(
    files: List[UploadFile] = File(...),
    intended_corrections: str = Form(...), # JSON string array of corrections
    db: AsyncSession = Depends(get_db)
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
            version_blocks.append(blocks)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to process {file.filename}: {str(e)}"
            )
            
    # Generate the Trust Report
    try:
        report = generate_trust_report(filenames, version_blocks, corrections_list)
        return {"report": report}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation engine failed: {str(e)}"
        )
