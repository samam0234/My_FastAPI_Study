"""HTTP 계층. 요청을 파싱해 service에 넘기고, service의 결과를 그대로 응답한다."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import Pagination, log_request_time
from app.posts import service
from app.posts.schemas import PaginatedPosts, PostCreate, PostResponse
from app.users.models import User
from app.users.service import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    dependencies=[Depends(log_request_time)],
)


@router.get("", response_model=PaginatedPosts)
def list_posts(
    published: Optional[bool] = Query(default=None, description="공개 여부로 필터링"),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
):
    return service.list_posts_paginated(db, published, pagination.skip, pagination.limit)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int = Path(..., gt=0, description="조회할 게시글 id"),
    db: Session = Depends(get_db),
):
    return service.get_post_or_404(db, post_id)


@router.post("", response_model=PostResponse, status_code=201)
def create_post(
    post: PostCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_post(db, post, current_user, background_tasks)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_post(db, post_id, post, current_user)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_post(db, post_id, current_user)
