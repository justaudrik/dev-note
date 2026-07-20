from sqlalchemy.orm import Session
from . import models


def has_document_access(user_id: int, doc_id: int, db: Session) -> bool:
    """Returns True if the user owns or is a collaborator on the document."""
    is_owner = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.user_id == user_id
    ).first() is not None

    if is_owner:
        return True

    return db.query(models.DocumentCollaborator).filter(
        models.DocumentCollaborator.document_id == doc_id,
        models.DocumentCollaborator.user_id == user_id
    ).first() is not None
