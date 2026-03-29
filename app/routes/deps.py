from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import User
from app.services import auth_service


def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = authorization.removeprefix("Bearer ").strip()
    user = auth_service.get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return user
