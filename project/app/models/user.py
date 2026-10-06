# ─────────────────────────────────────────────────────────────
# models/user.py : "users" 테이블과 대응하는 ORM 모델 (회원 정보)
# ─────────────────────────────────────────────────────────────
from sqlalchemy import Integer, String  # 컬럼 타입
from sqlalchemy.orm import Mapped, mapped_column  # 타입힌트 + 컬럼 옵션 지정 도구

from app.database import Base  # 모든 모델의 공통 부모


class User(Base):
    __tablename__ = "users"  # 실제 DB 테이블 이름

    # 기본키(PK) + 인덱스
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # unique=True: 같은 username을 가진 회원이 둘 이상 생기지 못하게 DB 차원에서 막는다.
    # index=True: 로그인 시 username으로 자주 검색하므로 인덱스로 속도를 높인다.
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # 비밀번호 "원문"이 아니라 해시(단방향 암호화)한 값만 저장한다 (보안).
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
