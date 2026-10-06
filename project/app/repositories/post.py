"""DB 접근 전용 계층. HTTP나 비즈니스 규칙은 전혀 모른다 — SQLAlchemy 쿼리만 다룬다."""

from typing import Optional

from sqlalchemy.orm import Session  # DB 작업 단위(트랜잭션)를 담당하는 세션 타입

from app.models.post import Post
from app.schemas.post import PostCreate


def list_all(db: Session) -> list[Post]:
    # db.query(Post): posts 테이블을 조회하는 쿼리 생성 / .all(): 모든 행을 리스트로 가져온다.
    #   SQL로는 SELECT * FROM posts 와 같다.
    return db.query(Post).all()


def get_by_id(db: Session, post_id: int) -> Optional[Post]:
    # db.get(모델, 기본키): 기본키(id)로 한 건을 조회한다. 없으면 None을 반환한다.
    return db.get(Post, post_id)


def create(db: Session, post: PostCreate, author_id: int) -> Post:
    # post.model_dump(): Pydantic 객체 → dict ({"title":..., "content":..., "published":...})
    # **dict : 딕셔너리를 키워드 인자로 풀어서 넘긴다 → Post(title=..., content=..., ...)
    new_post = Post(**post.model_dump(), author_id=author_id)
    db.add(new_post)  # 세션에 "저장 예정" 객체로 등록 (아직 DB에는 반영 안 됨)
    db.commit()  # 변경사항을 DB에 확정(INSERT 실행)
    db.refresh(new_post)  # DB에서 다시 읽어 자동 생성된 값(id 등)을 객체에 채운다
    return new_post


def update(db: Session, post: Post, data: PostCreate) -> Post:
    # 조회해 둔 ORM 객체의 속성을 바꾸면 SQLAlchemy가 변경을 감지해 UPDATE를 만든다.
    post.title = data.title
    post.content = data.content
    post.published = data.published
    db.commit()  # 변경 확정
    db.refresh(post)  # 최신 상태로 다시 읽기
    return post


def delete(db: Session, post: Post) -> None:
    db.delete(post)  # 삭제 예정으로 표시
    db.commit()  # DELETE 확정
