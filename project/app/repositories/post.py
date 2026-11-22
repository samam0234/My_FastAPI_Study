"""posts 테이블 접근. 검색·정렬·offset/limit만 수행한다."""

import json
from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.post import Post
from app.schemas.post import PostCreate, PostPatch

_SORTS = {"createdAt", "-createdAt", "-commentCount"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def dump_tags(tags: list[str]) -> str:
    return json.dumps(tags, ensure_ascii=False)


def load_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def is_allowed_sort(sort: str) -> bool:
    return sort in _SORTS


def get_by_id(db: Session, post_id: int) -> Post | None:
    return db.get(Post, post_id)


def _filtered(db: Session, q: str):
    query = db.query(Post)
    keyword = q.strip()
    if keyword:
        pattern = f"%{keyword.lower()}%"
        query = query.filter(
            or_(func.lower(Post.title).like(pattern), func.lower(Post.body).like(pattern))
        )
    return query


def search(db: Session, *, q: str, sort: str, offset: int, limit: int) -> tuple[list[Post], int]:
    filtered = _filtered(db, q)
    total = filtered.count()
    if sort == "createdAt":
        ordered = filtered.order_by(Post.created_at.asc(), Post.id.asc())
    elif sort == "-commentCount":
        counts = (
            db.query(Comment.post_id.label("post_id"), func.count(Comment.id).label("cnt"))
            .group_by(Comment.post_id)
            .subquery()
        )
        ordered = filtered.outerjoin(counts, Post.id == counts.c.post_id).order_by(
            func.coalesce(counts.c.cnt, 0).desc(),
            Post.created_at.desc(),
        )
    else:
        ordered = filtered.order_by(Post.created_at.desc(), Post.id.desc())
    return ordered.offset(offset).limit(limit).all(), total


def create(db: Session, data: PostCreate, author_id: int) -> Post:
    now = utcnow()
    post = Post(
        title=data.title,
        body=data.body,
        tags=dump_tags(data.tags),
        author_id=author_id,
        created_at=now,
        updated_at=now,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def update(db: Session, post: Post, data: PostPatch) -> Post:
    changes = data.model_dump(exclude_unset=True)
    if "title" in changes:
        post.title = changes["title"]
    if "body" in changes:
        post.body = changes["body"]
    if "tags" in changes and changes["tags"] is not None:
        post.tags = dump_tags(changes["tags"])
    post.updated_at = utcnow()
    db.commit()
    db.refresh(post)
    return post


def delete(db: Session, post: Post) -> None:
    db.query(Comment).filter(Comment.post_id == post.id).delete()
    db.delete(post)
    db.commit()
