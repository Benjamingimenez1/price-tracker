from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database.session import get_db
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    result = auth_service.register(db, body.email, body.username, body.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    result = auth_service.login(db, body.email, body.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result
