from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import store
from app.database import get_db
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return store.create_user(db, user)
