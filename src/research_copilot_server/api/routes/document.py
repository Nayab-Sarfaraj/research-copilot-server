from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from research_copilot_server.config.db import get_db
from research_copilot_server.dependencies.auth import get_current_user
from research_copilot_server.models.user import User
from research_copilot_server.schema.document import DocumentResponse
from research_copilot_server.services import document as document_service

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse, include_in_schema=False)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Upload a PDF, split it into chunk records, and save each chunk with its embedding."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    contents = await file.read()
    documents = document_service.process_pdf_document(
        db,
        file.filename,
        contents,
        user_id=current_user.id,
    )

    return {
        "filename": file.filename,
        "saved_chunk_count": len(documents),
        "chunks": [
            {
                "content": document.content,
                "metadata": document.document_metadata,
                "embedding_length": len(document.embedding) if document.embedding else 0,
            }
            for document in documents
        ],
    }
