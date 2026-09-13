"""HTTP 계층. 요청을 파싱해 services에 넘기고, services의 결과를 그대로 응답한다."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services import user as service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return service.register_user(db, user)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return service.authenticate(db, form_data.username, form_data.password)
