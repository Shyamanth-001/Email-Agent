import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import RefreshToken, User

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt-key-change-in-production")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


# ==================================================
# Password Hashing & Email Normalization
# ==================================================

def normalize_email(email: str) -> str:
    """Normalize email address by stripping whitespace and lowercasing."""
    return email.strip().lower()


def hash_password(password: str) -> str:
    """Hash a password securely using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a raw password against its bcrypt hash."""
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


# ==================================================
# JWT Access Tokens (15 Minutes)
# ==================================================

def create_access_token(user: User) -> str:
    """Create a short-lived JWT access token (15 minutes)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256",
    )


# ==================================================
# Refresh Tokens & Rotation (7 Days, Hash Stored)
# ==================================================

def hash_refresh_token(raw_token: str) -> str:
    """Compute SHA-256 hash of raw refresh token for database storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_refresh_token(
    db: Session,
    user_id: int,
    token_family_id: str | None = None,
) -> tuple[str, RefreshToken]:
    """
    Generate a cryptographically random refresh token,
    store only its SHA-256 hash in PostgreSQL, and return (raw_token, db_record).
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(raw_token)
    family_id = token_family_id or str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_record = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        token_family_id=family_id,
    )
    db.add(refresh_record)
    db.commit()
    db.refresh(refresh_record)

    return raw_token, refresh_record


def verify_and_rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> tuple[str, str, User]:
    """
    Validate refresh token, rotate it, detect reuse, and return (new_raw_refresh_token, new_access_token, user).
    If reuse of a revoked token is detected, revoke the entire token family.
    """
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    token_hash = hash_refresh_token(raw_token)
    token_record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # REUSE DETECTION: if token is already revoked or replaced, revoke family!
    if token_record.revoked_at is not None or token_record.replaced_by_token_id is not None:
        now = datetime.now(timezone.utc)
        active_family_tokens = db.scalars(
            select(RefreshToken).where(
                RefreshToken.token_family_id == token_record.token_family_id,
                RefreshToken.revoked_at.is_(None),
            )
        ).all()
        for tok in active_family_tokens:
            tok.revoked_at = now
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. Session revoked.",
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    exp = token_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp <= now:
        token_record.revoked_at = now
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Check user
    user = db.scalar(select(User).where(User.id == token_record.user_id))
    if not user or not user.is_active:
        token_record.revoked_at = now
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
        )

    # ROTATION: revoke current token, generate new refresh token in same family
    new_raw_token, new_record = create_refresh_token(
        db,
        user_id=user.id,
        token_family_id=token_record.token_family_id,
    )

    token_record.revoked_at = now
    token_record.replaced_by_token_id = new_record.id
    db.commit()

    new_access_token = create_access_token(user)

    return new_raw_token, new_access_token, user


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    """Revoke a refresh token server-side upon logout."""
    if not raw_token:
        return
    token_hash = hash_refresh_token(raw_token)
    token_record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if token_record and token_record.revoked_at is None:
        token_record.revoked_at = datetime.now(timezone.utc)
        db.commit()


# ==================================================
# Google ID Token Verification
# ==================================================

def verify_google_token(credential: str) -> dict:
    """Verify Google OAuth ID token server-side matching GOOGLE_CLIENT_ID."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured on server",
        )
    try:
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
        return info
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(err)}",
        )


# ==================================================
# FastAPI Dependency — Get Current User
# ==================================================

def get_current_user_from_db(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(lambda: None),
) -> User:
    """Extract Bearer JWT, verify signature & expiration, and retrieve active user."""
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = db.scalar(select(User).where(User.id == int(user_id)))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user