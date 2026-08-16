import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..email_utils import send_verification_email
import app

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _build_verify_url(request: Request, token: str) -> str:
    """Build the verification URL using APP_URL if set, otherwise from the request."""
    override = os.getenv("APP_URL", "").strip().rstrip("/")
    base = override if override else str(request.base_url).rstrip("/")
    return f"{base}/?verify={token}"


# ── Register ──────────────────────────────────────────────────────────────────

# temporary dummy route to test that the server is alive and routing works
@app.get("/api/auth/ping")
def ping_test():
    return {"status": "success", "message": "The server is alive and routing works!"}

@router.post("/register", status_code=202)
def register(
    user_data: schemas.UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        """
        Create an unverified account and send a verification email.
        Returns 202 Accepted — the account cannot log in until the email is verified.
        """
        if db.query(models.User).filter(models.User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        if db.query(models.User).filter(models.User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")

        verification_token = str(uuid.uuid4())

        user = models.User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            is_verified=False,
            verification_token=verification_token
        )
        db.add(user)
        db.commit()

        verify_url = _build_verify_url(request, verification_token)
        email_sent = send_verification_email(
            to_email=user_data.email,
            username=user_data.username,
            verify_url=verify_url
        )  

        return {
            "message": "Account created. Please check your email to verify before logging in.",
            "email_sent": email_sent,
            # verify_url is returned ONLY when SMTP isn't configured — useful for local dev
            "verify_url": verify_url if not email_sent else None
        }
    except Exception as e:
        # This will print the error to Render's logs
        print("CRITICAL ERROR IN REGISTER ROUTE:")
        traceback.print_exc()
        
        # This forces the exact error string directly into your browser!
        raise HTTPException(status_code=500, detail=f"DEBUG ERROR: {str(e)}")


# ── Verify email ──────────────────────────────────────────────────────────────

@router.get("/verify/{token}", response_model=schemas.Token)
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Process an email verification link.
    Activates the account and returns a JWT so the user is immediately logged in.
    """
    user = db.query(models.User).filter(
        models.User.verification_token == token,
        models.User.is_verified == False
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="This verification link is invalid or has already been used."
        )

    user.is_verified = True
    user.verification_token = None   # Consume the token — one-time use
    db.commit()

    jwt_token = create_access_token(data={"sub": user.email})
    return {"access_token": jwt_token, "token_type": "bearer"}


# ── Resend verification ───────────────────────────────────────────────────────

@router.post("/resend-verification")
def resend_verification(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Issue a new verification token and resend the email.
    Always returns the same generic message — never reveals whether the email exists.
    """
    email = payload.get("email", "").strip()

    user = db.query(models.User).filter(
        models.User.email == email,
        models.User.is_verified == False
    ).first()

    generic = {"message": "If that email belongs to an unverified account, a new link has been sent."}

    if not user:
        return generic

    user.verification_token = str(uuid.uuid4())
    db.commit()

    verify_url = _build_verify_url(request, user.verification_token)
    send_verification_email(to_email=email, username=user.username, verify_url=verify_url)

    # Return verify_url only when SMTP is not configured
    email_sent = bool(os.getenv("SMTP_HOST"))
    return {**generic, "verify_url": verify_url if not email_sent else None}


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_verified:
        # Use a machine-readable code so the frontend can show a contextual message
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="EMAIL_NOT_VERIFIED"
        )

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user