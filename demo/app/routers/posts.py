import time
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from sqlalchemy.orm import Session

from app import store
from app.database import get_db
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
    db: Session = Depends(get_db),
):
    result = store.list_posts(db)
    if published is not None:
        result = [p for p in result if p.published == published]
    return result[pagination.skip : pagination.skip + pagination.limit]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int = Path(..., gt=0, description="조회할 게시글 id"),
    db: Session = Depends(get_db),
):
    return store.get_post_or_404(db, post_id)


def notify_new_post(title: str) -> None:
    """새 글 알림 발송을 흉내내는 느린 작업(예: 이메일/웹훅 호출)."""
    time.sleep(1)
    print(f"[background] notified about new post: {title}")


@router.post("", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    created = store.create_post(db, post)
    # response_model 직렬화 이후, 응답을 클라이언트로 보낸 뒤에 실행된다.
    # 클라이언트는 notify_new_post()가 끝나기를 기다리지 않는다.
    background_tasks.add_task(notify_new_post, created.title)
    return created


@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: PostCreate, db: Session = Depends(get_db)):
    return store.update_post(db, post_id, post)


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    store.delete_post(db, post_id)
