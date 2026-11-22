"""댓글 HTTP."""

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import PageParams
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentEnvelope, CommentList
from app.services import comment as service
from app.services.user import get_current_user

router = APIRouter(tags=["comments"])


@router.get("/posts/{post_id}/comments", response_model=CommentList)
def list_comments(
    post_id: int = Path(..., gt=0),
    page: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    return service.list_comments(db, post_id, page.page, page.limit)


@router.post("/posts/{post_id}/comments", response_model=CommentEnvelope, status_code=status.HTTP_201_CREATED)
def create_comment(
    payload: CommentCreate,
    post_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CommentEnvelope(data=service.create_comment(db, post_id, payload, current_user))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_comment(db, comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
