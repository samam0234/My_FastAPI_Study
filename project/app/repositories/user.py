"""users 테이블 접근. 해시와 중복 메시지는 서비스가 담당한다."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_many(db: Session, user_ids: set[int]) -> dict[int, User]:
    if not user_ids:
        return {}
    rows = db.query(User).filter(User.id.in_(user_ids)).all()
    return {row.id: row for row in rows}


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create(db: Session, email: str, nickname: str, hashed_password: str) -> User:
    user = User(email=email, nickname=nickname, hashed_password=hashed_password)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user
