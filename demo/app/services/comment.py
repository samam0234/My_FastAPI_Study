"""댓글 규칙. 글이 없으면 404, 남의 댓글 삭제는 403."""

from fastapi import status
from sqlalchemy.orm import Session

from app.cache import cache_clear
from app.errors import AppError
from app.models.user import User
from app.repositories import comment as repository
from app.repositories import user as user_repository
from app.schemas.comment import CommentCreate, CommentList, CommentResponse
from app.schemas.post import Author, PageMeta
from app.services.post import get_post_or_404


def _present(db: Session, comments) -> list[CommentResponse]:
    authors = user_repository.get_many(
        db, {comment.author_id for comment in comments if comment.author_id is not None}
    )
    result: list[CommentResponse] = []
    for comment in comments:
        author = authors.get(comment.author_id) if comment.author_id is not None else None
        result.append(
            CommentResponse(
                id=comment.id,
                post_id=comment.post_id,
                body=comment.body,
                author=Author(id=author.id, nickname=author.nickname) if author else None,
                created_at=comment.created_at,
            )
        )
    return result


def list_comments(db: Session, post_id: int, page: int, limit: int) -> CommentList:
    get_post_or_404(db, post_id)
    offset = (page - 1) * limit
    rows, total = repository.list_for_post(db, post_id, offset, limit)
    total_pages = (total + limit - 1) // limit if total else 0
    return CommentList(
        data=_present(db, rows),
        meta=PageMeta(page=page, limit=limit, total=total, total_pages=total_pages, q=""),
    )


def create_comment(db: Session, post_id: int, data: CommentCreate, author: User) -> CommentResponse:
    get_post_or_404(db, post_id)
    created = repository.create(db, post_id, author.id, data.body.strip())
    cache_clear()
    return _present(db, [created])[0]


def delete_comment(db: Session, comment_id: int, current_user: User) -> None:
    comment = repository.get_by_id(db, comment_id)
    if comment is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "해당 댓글을 찾을 수 없습니다.")
    if comment.author_id != current_user.id:
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "작성자만 수정하거나 삭제할 수 있습니다.")
    repository.delete(db, comment)
    cache_clear()
