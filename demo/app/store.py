from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models
from app.schemas import PostCreate


def list_posts(db: Session) -> list[models.Post]:
    return db.query(models.Post).all()


def get_post_or_404(db: Session, post_id: int) -> models.Post:
    post = db.get(models.Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")
    return post


def create_post(db: Session, post: PostCreate) -> models.Post:
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def update_post(db: Session, post_id: int, post: PostCreate) -> models.Post:
    existing = get_post_or_404(db, post_id)
    existing.title = post.title
    existing.content = post.content
    existing.published = post.published
    db.commit()
    db.refresh(existing)
    return existing


def delete_post(db: Session, post_id: int) -> None:
    existing = get_post_or_404(db, post_id)
    db.delete(existing)
    db.commit()
