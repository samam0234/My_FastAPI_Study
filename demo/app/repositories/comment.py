"""comments 테이블 접근."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.comment import Comment


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_by_id(db: Session, comment_id: int) -> Comment | None:
    return db.get(Comment, comment_id)


def list_for_post(db: Session, post_id: int, offset: int, limit: int) -> tuple[list[Comment], int]:
    query = db.query(Comment).filter(Comment.post_id == post_id)
    total = query.count()
    rows = query.order_by(Comment.created_at.asc(), Comment.id.asc()).offset(offset).limit(limit).all()
    return rows, total


def count_for_posts(db: Session, post_ids: list[int]) -> dict[int, int]:
    if not post_ids:
        return {}
    rows = (
        db.query(Comment.post_id, func.count(Comment.id))
        .filter(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
        .all()
    )
    return {post_id: count for post_id, count in rows}


def create(db: Session, post_id: int, author_id: int, body: str) -> Comment:
    comment = Comment(post_id=post_id, author_id=author_id, body=body, created_at=utcnow())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.commit()
