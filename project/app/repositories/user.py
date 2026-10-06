"""DB 접근 전용 계층. HTTP나 비즈니스 규칙(중복 검사 등)은 전혀 모른다."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User


def get_by_username(db: Session, username: str) -> Optional[User]:
    # .filter(조건): WHERE 절 (User.username == username 이면 SQL의 username = '...' 과 같다)
    # .first(): 조건에 맞는 첫 번째 행만 가져오고, 없으면 None을 반환한다.
    return db.query(User).filter(User.username == username).first()


def create(db: Session, username: str, hashed_password: str) -> User:
    # 이미 해시된 비밀번호를 받아 저장만 한다 (해싱은 services 계층의 책임).
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)  # 저장 예정 등록
    db.commit()  # INSERT 확정
    db.refresh(new_user)  # DB가 만들어준 id 등을 다시 읽어 채운다
    return new_user
