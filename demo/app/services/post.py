"""비즈니스 로직 계층. repositories(DB)와 routers(HTTP) 사이에서 규칙을 담당한다."""

import time
from typing import Optional

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User
from app.repositories import post as repository
from app.schemas.post import PaginatedPosts, PostCreate


def get_post_or_404(db: Session, post_id: int) -> Post:
    post = repository.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")
    return post


def list_posts_paginated(
    db: Session, published: Optional[bool], skip: int, limit: int
) -> PaginatedPosts:
    result = repository.list_all(db)
    if published is not None:
        result = [p for p in result if p.published == published]
    page = result[skip : skip + limit]
    return PaginatedPosts(items=page, total=len(result), skip=skip, limit=limit)


def _notify_new_post(title: str) -> None:
    """새 글 알림 발송을 흉내내는 느린 작업(예: 이메일/웹훅 호출)."""
    time.sleep(1)
    print(f"[background] notified about new post: {title}")


def create_post(
    db: Session, post: PostCreate, author: User, background_tasks: BackgroundTasks
) -> Post:
    created = repository.create(db, post, author_id=author.id)
    # 응답을 클라이언트로 보낸 뒤에 실행된다 — 클라이언트는 알림 발송을 기다리지 않는다.
    background_tasks.add_task(_notify_new_post, created.title)
    return created


def _check_owner(post: Post, current_user: User) -> None:
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 글만 수정/삭제할 수 있습니다.",
        )


def update_post(db: Session, post_id: int, data: PostCreate, current_user: User) -> Post:
    existing = get_post_or_404(db, post_id)
    _check_owner(existing, current_user)
    return repository.update(db, existing, data)


def delete_post(db: Session, post_id: int, current_user: User) -> None:
    existing = get_post_or_404(db, post_id)
    _check_owner(existing, current_user)
    repository.delete(db, existing)
