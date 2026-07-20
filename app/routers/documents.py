from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..utils import has_document_access

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/", response_model=List[schemas.DocumentResponse])
def list_documents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all documents the user owns OR is a collaborator on."""
    collab_ids = (
        db.query(models.DocumentCollaborator.document_id)
        .filter(models.DocumentCollaborator.user_id == current_user.id)
        .subquery()
    )
    return (
        db.query(models.Document)
        .filter(
            or_(
                models.Document.user_id == current_user.id,
                models.Document.id.in_(collab_ids)
            )
        )
        .order_by(models.Document.is_pinned.desc(), models.Document.updated_at.desc())
        .all()
    )


@router.post("/", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    doc_data: schemas.DocumentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = models.Document(
        user_id=current_user.id,
        title=doc_data.title,
        content=doc_data.content,
        format=doc_data.format
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/{doc_id}", response_model=schemas.DocumentResponse)
def get_document(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not has_document_access(current_user.id, doc_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return document


@router.put("/{doc_id}", response_model=schemas.DocumentResponse)
def update_document(
    doc_id: int,
    doc_data: schemas.DocumentUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not has_document_access(current_user.id, doc_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    if doc_data.title is not None:
        document.title = doc_data.title
    if doc_data.content is not None:
        document.content = doc_data.content
    if doc_data.format is not None:
        document.format = doc_data.format
    if doc_data.is_pinned is not None:
        document.is_pinned = doc_data.is_pinned

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Only the document owner can delete."""
    document = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found or not owner")
    db.delete(document)
    db.commit()
