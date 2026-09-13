from typing import Optional

from fastapi import APIRouter, Depends, Path, Query

from app import store
from app.dependencies import Pagination, log_request_time
from app.schemas import PostCreate, PostResponse

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    dependencies=[Depends(log_request_time)],
)


@router.get("", response_model=list[PostResponse])
def list_posts(
    published: Optional[bool] = Query(default=None, description="공개 여부로 필터링"),
    pagination: Pagination = Depends(),
):
    result = store.list_posts()
    if published is not None:
        result = [p for p in result if p.published == published]
    return result[pagination.skip : pagination.skip + pagination.limit]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int = Path(..., gt=0, description="조회할 게시글 id")):
    return store.get_post_or_404(post_id)


@router.post("", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate):
    return store.create_post(post)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: PostCreate):
    return store.update_post(post_id, post)


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int):
    store.delete_post(post_id)
