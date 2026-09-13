"""DB 접근 전용 계층. HTTP나 비즈니스 규칙은 전혀 모른다 — SQLAlchemy 쿼리만 다룬다."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.post import Post
from app.schemas.post import PostCreate


def list_all(db: Session) -> list[Post]:
    return db.query(Post).all()


def get_by_id(db: Session, post_id: int) -> Optional[Post]:
    return db.get(Post, post_id)


def create(db: Session, post: PostCreate, author_id: int) -> Post:
    new_post = Post(**post.model_dump(), author_id=author_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def update(db: Session, post: Post, data: PostCreate) -> Post:
    post.title = data.title
    post.content = data.content
    post.published = data.published
    db.commit()
    db.refresh(post)
    return post


def delete(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()
