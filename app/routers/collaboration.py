import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError, jwt

from .. import models
from ..database import get_db
from ..auth import get_current_user, SECRET_KEY, ALGORITHM
from ..connection_manager import manager
from ..email_utils import send_share_email
from ..utils import has_document_access

router = APIRouter(tags=["collaboration"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_user_from_token(token: str, db: Session) -> Optional[models.User]:
    """Verify a JWT and return the User — used for WebSocket auth."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
        return db.query(models.User).filter(models.User.email == email).first()
    except JWTError:
        return None


def build_base_url(request: Request) -> str:
    """
    Return the base URL for share links.

    Priority:
      1. APP_URL env var  — set this in .env for production (Railway, etc.)
      2. Auto-detected    — derived from the incoming request, works correctly
                            for localhost, LAN IPs, and public hosts alike.
    """
    override = os.getenv("APP_URL", "").strip().rstrip("/")
    if override:
        return override
    # request.base_url gives e.g. "http://192.168.1.10:8000/"
    return str(request.base_url).rstrip("/")


# ── Share link ────────────────────────────────────────────────────────────────

@router.post("/api/collab/{doc_id}/share")
def create_share_link(
    doc_id: int,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate (or retrieve) a shareable link. The URL reflects the actual host."""
    if not has_document_access(current_user.id, doc_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    existing = db.query(models.ShareLink).filter(
        models.ShareLink.document_id == doc_id
    ).first()

    if existing:
        token = existing.token
    else:
        token = str(uuid.uuid4())
        db.add(models.ShareLink(
            document_id=doc_id, token=token, created_by=current_user.id
        ))
        db.commit()

    base = build_base_url(request)
    return {"token": token, "url": f"{base}/dashboard?join={token}"}


@router.post("/api/collab/join/{token}")
def join_via_link(
    token: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a share link — add the current user as a collaborator."""
    link = db.query(models.ShareLink).filter(models.ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")

    doc = db.query(models.Document).filter(models.Document.id == link.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document no longer exists")

    if doc.user_id == current_user.id:
        return {"document_id": doc.id, "title": doc.title, "role": "owner"}

    already = db.query(models.DocumentCollaborator).filter(
        models.DocumentCollaborator.document_id == doc.id,
        models.DocumentCollaborator.user_id == current_user.id
    ).first()

    if not already:
        db.add(models.DocumentCollaborator(
            document_id=doc.id, user_id=current_user.id
        ))
        db.commit()

    return {"document_id": doc.id, "title": doc.title, "role": "collaborator"}


@router.post("/api/collab/{doc_id}/invite")
def invite_by_email(
    doc_id: int,
    payload: dict,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send an email invitation. Gracefully skips if SMTP is not configured."""
    if not has_document_access(current_user.id, doc_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    to_email = payload.get("email", "").strip()
    if not to_email:
        raise HTTPException(status_code=400, detail="Email is required")

    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    link = db.query(models.ShareLink).filter(
        models.ShareLink.document_id == doc_id
    ).first()
    if not link:
        token = str(uuid.uuid4())
        link = models.ShareLink(
            document_id=doc_id, token=token, created_by=current_user.id
        )
        db.add(link)
        db.commit()

    base = build_base_url(request)
    share_url = f"{base}/dashboard?join={link.token}"

    email_sent = send_share_email(
        to_email=to_email,
        sharer_name=current_user.username,
        doc_title=doc.title,
        share_url=share_url
    )

    return {
        "email_sent": email_sent,
        "share_url": share_url,
        "note": "SMTP not configured — share the link manually." if not email_sent else None
    }


@router.get("/api/collab/{doc_id}/collaborators")
def list_collaborators(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not has_document_access(current_user.id, doc_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    owner = db.query(models.User).filter(models.User.id == doc.user_id).first()

    rows = (
        db.query(models.DocumentCollaborator, models.User)
        .join(models.User, models.DocumentCollaborator.user_id == models.User.id)
        .filter(models.DocumentCollaborator.document_id == doc_id)
        .all()
    )

    return {
        "owner": {"id": owner.id, "username": owner.username, "email": owner.email},
        "collaborators": [
            {"id": u.id, "username": u.username, "email": u.email}
            for _, u in rows
        ]
    }


# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/ws/{doc_id}")
async def websocket_collab(
    websocket: WebSocket,
    doc_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Real-time collaborative editing.

    Connect:  ws://host/ws/{doc_id}?token={jwt}

    Client → Server:
      { "type": "edit", "content": "...", "save": false }           broadcast only
      { "type": "edit", "content": "...", "save": true, "title": "..." }  + DB write

    Server → Client:
      { "type": "edit",     "content": "...", "by": "username" }
      { "type": "presence", "users": [...],   "count": N }
      { "type": "saved" }
    """
    user = get_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    if not has_document_access(user.id, doc_id, db):
        await websocket.close(code=4003, reason="Forbidden")
        return

    await manager.connect(websocket, doc_id, user.username)
    usernames = manager.get_usernames(doc_id)
    await manager.broadcast_to_all(
        {"type": "presence", "users": usernames, "count": len(usernames)},
        doc_id
    )

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "edit":
                content = data.get("content", "")

                # Broadcast immediately to every other connected client
                await manager.broadcast_to_others(
                    {"type": "edit", "content": content, "by": user.username},
                    doc_id,
                    sender=websocket
                )

                # Persist to DB only on save checkpoints (every 1.5s from client)
                if data.get("save"):
                    doc = db.query(models.Document).filter(
                        models.Document.id == doc_id
                    ).first()
                    if doc:
                        doc.content = content
                        if data.get("title"):
                            doc.title = data["title"]
                        db.commit()
                    await websocket.send_json({"type": "saved"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, doc_id)
        remaining = manager.get_usernames(doc_id)
        await manager.broadcast_to_all(
            {"type": "presence", "users": remaining, "count": len(remaining)},
            doc_id
        )
