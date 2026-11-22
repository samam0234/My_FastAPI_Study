"""게시글 HTTP. 이 라우터의 prefix는 /posts 이고, 앱에서 /api 를 한 번 더 붙인다."""

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Path, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import PageParams, log_request_time
from app.models.user import User
from app.schemas.post import PostCreate, PostEnvelope, PostList, PostPatch
from app.services import post as service
from app.services.user import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    dependencies=[Depends(log_request_time)],
)


@router.get("", response_model=PostList)
def list_posts(page: PageParams = Depends(), db: Session = Depends(get_db)):
    return service.list_posts(db, q=page.q, sort=page.sort, page=page.page, limit=page.limit)


@router.get("/{post_id}", response_model=PostEnvelope)
def get_post(post_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    return PostEnvelope(data=service.present_one(db, service.get_post_or_404(db, post_id)))


@router.post("", response_model=PostEnvelope, status_code=status.HTTP_201_CREATED)
def create_post(
    post: PostCreate,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    created = service.create_post(db, post, current_user, background_tasks, idempotency_key)
    response.headers["Location"] = f"/api/posts/{created.id}"
    return PostEnvelope(data=created)


@router.patch("/{post_id}", response_model=PostEnvelope)
def update_post(
    payload: PostPatch,
    post_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PostEnvelope(data=service.update_post(db, post_id, payload, current_user))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_post(db, post_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
