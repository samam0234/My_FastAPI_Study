from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models
from app.schemas import PostCreate, UserCreate
from app.security import hash_password


def list_posts(db: Session) -> list[models.Post]:
    return db.query(models.Post).all()


def get_post_or_404(db: Session, post_id: int) -> models.Post:
    post = db.get(models.Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")
    return post


def create_post(db: Session, post: PostCreate, author_id: int) -> models.Post:
    new_post = models.Post(**post.model_dump(), author_id=author_id)
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


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: UserCreate) -> models.User:
    if get_user_by_username(db, user.username) is not None:
        raise HTTPException(status_code=400, detail="이미 존재하는 username입니다.")
    new_user = models.User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
