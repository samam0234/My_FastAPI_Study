"""DB 접근 전용 계층. HTTP나 비즈니스 규칙(중복 검사 등)은 전혀 모른다."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User


def get_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create(db: Session, username: str, hashed_password: str) -> User:
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
