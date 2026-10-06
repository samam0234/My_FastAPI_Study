# ─────────────────────────────────────────────────────────────
# models/post.py : "posts" 테이블과 1:1로 대응하는 SQLAlchemy ORM 모델
#   ORM = 테이블의 행(row)을 파이썬 객체로 다루게 해주는 기술.
# ─────────────────────────────────────────────────────────────
from typing import Optional  # Optional[X] = "X 또는 None" 을 허용한다는 타입 표기

# 컬럼 타입(Boolean/Integer/String)과 외래키(ForeignKey) 정의 도구
from sqlalchemy import Boolean, ForeignKey, Integer, String

# Mapped: 컬럼의 파이썬 타입을 표기하는 SQLAlchemy 2.0 방식의 타입힌트
# mapped_column: 실제 컬럼의 옵션(PK, 길이, NULL 허용 등)을 지정하는 함수
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base  # 모든 모델의 공통 부모


# Base를 상속하면 이 클래스가 DB 테이블 정의로 등록된다.
class Post(Base):
    __tablename__ = "posts"  # 실제 DB에 만들어질 테이블 이름

    # primary_key=True: 각 행을 구분하는 고유 번호(기본키). 정수 PK는 자동 증가한다.
    # index=True: 이 컬럼에 인덱스를 만들어 검색 속도를 높인다.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # String(200): 최대 200자 문자열 / nullable=False: NULL(빈 값) 저장 불가 → 필수 입력
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 길이 제한 없는 문자열 (본문)
    content: Mapped[str] = mapped_column(String, nullable=False)
    # default=True: 값을 안 주면 공개(True)로 저장된다.
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    # ForeignKey("users.id"): users 테이블의 id를 참조하는 외래키 → 이 글을 쓴 작성자.
    # nullable=True: 작성자가 없는 글(예: 초기 시드 데이터)도 허용한다.
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
