import hashlib
import hmac
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import User
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TOKEN_TTL_HOURS = 24 * 7  # 7 days


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}:{hashed.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":", 1)
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
        return hmac.compare_digest(check.hex(), hashed)
    except Exception:
        return False


def _make_token(user_id: int) -> str:
    """Simple HMAC token: user_id|timestamp|hmac"""
    ts = int(datetime.now(timezone.utc).timestamp())
    payload = f"{user_id}|{ts}"
    sig = hmac.new(settings.secret_key.encode(), payload.encode(), "sha256").hexdigest()
    return f"{payload}|{sig}"


def _verify_token(token: str) -> Optional[int]:
    try:
        parts = token.split("|")
        if len(parts) != 3:
            return None
        user_id, ts, sig = parts
        payload = f"{user_id}|{ts}"
        expected = hmac.new(settings.secret_key.encode(), payload.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        # Check expiry
        age = datetime.now(timezone.utc).timestamp() - int(ts)
        if age > TOKEN_TTL_HOURS * 3600:
            return None
        return int(user_id)
    except Exception:
        return None


def register(db: Session, email: str, username: str, password: str) -> dict:
    if db.query(User).filter(User.email == email).first():
        return {"success": False, "error": "Email ya registrado"}
    if db.query(User).filter(User.username == username).first():
        return {"success": False, "error": "Username ya en uso"}

    user = User(
        email=email,
        username=username,
        hashed_pw=_hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = _make_token(user.id)
    return {"success": True, "token": token, "user_id": user.id, "username": username}


def login(db: Session, email: str, password: str) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user or not _verify_password(password, user.hashed_pw):
        return {"success": False, "error": "Credenciales inválidas"}
    token = _make_token(user.id)
    return {"success": True, "token": token, "user_id": user.id, "username": user.username}


def get_user_from_token(db: Session, token: str) -> Optional[User]:
    user_id = _verify_token(token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()
