"""게시글 규칙. 없으면 404, 남의 글이면 403. 이 순서를 바꾸지 않는다."""

from fastapi import BackgroundTasks, status
from sqlalchemy.orm import Session

from app.cache import cache_clear, cache_get, cache_set
from app.errors import AppError
from app.models.post import Post
from app.models.user import User
from app.repositories import comment as comment_repository
from app.repositories import post as repository
from app.repositories import user as user_repository
from app.schemas.post import Author, PageMeta, PostCreate, PostList, PostPatch, PostResponse

_idempotency: dict[str, int] = {}


def reset_idempotency() -> None:
    _idempotency.clear()
    cache_clear()


def _author_map(db: Session, posts: list[Post]) -> dict[int, User]:
    return user_repository.get_many(db, {post.author_id for post in posts if post.author_id is not None})


def present_many(db: Session, posts: list[Post]) -> list[PostResponse]:
    authors = _author_map(db, posts)
    counts = comment_repository.count_for_posts(db, [post.id for post in posts])
    result: list[PostResponse] = []
    for post in posts:
        author = authors.get(post.author_id) if post.author_id is not None else None
        result.append(
            PostResponse(
                id=post.id,
                title=post.title,
                body=post.body,
                tags=repository.load_tags(post.tags),
                author=Author(id=author.id, nickname=author.nickname) if author else None,
                comment_count=counts.get(post.id, 0),
                created_at=post.created_at,
                updated_at=post.updated_at,
            )
        )
    return result


def present_one(db: Session, post: Post) -> PostResponse:
    return present_many(db, [post])[0]


def get_post_or_404(db: Session, post_id: int) -> Post:
    post = repository.get_by_id(db, post_id)
    if post is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "해당 게시글을 찾을 수 없습니다.")
    return post


def _check_owner(post: Post, current_user: User) -> None:
    if post.author_id != current_user.id:
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "작성자만 수정하거나 삭제할 수 있습니다.")


def _notify_new_post(title: str) -> None:
    """응답을 보낸 뒤에 도는 알림 자리. 실제 메일은 study13에서 이 함수를 바꾼다."""
    print(f"[background] notified about new post: {title}")


async def _publish_post_created(post_id: int) -> None:
    """실시간 연결이 있는 앱이면 글 id만 보낸다. demo에는 realtime 모듈이 없다."""
    try:
        from app.realtime import hub
    except ModuleNotFoundError:
        return
    await hub.broadcast({"event": "post.created", "id": post_id})


def list_posts(db: Session, *, q: str, sort: str, page: int, limit: int) -> PostList:
    if not repository.is_allowed_sort(sort):
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "BAD_REQUEST",
            "sort는 createdAt, -createdAt, -commentCount 중 하나여야 합니다.",
        )
    cache_key = f"posts:{q}:{sort}:{page}:{limit}"
    cached = cache_get(cache_key)
    if isinstance(cached, PostList):
        return cached
    offset = (page - 1) * limit
    rows, total = repository.search(db, q=q, sort=sort, offset=offset, limit=limit)
    total_pages = (total + limit - 1) // limit if total else 0
    payload = PostList(
        data=present_many(db, rows),
        meta=PageMeta(page=page, limit=limit, total=total, total_pages=total_pages, q=q),
    )
    cache_set(cache_key, payload)
    return payload


def create_post(
    db: Session,
    data: PostCreate,
    author: User,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = None,
) -> PostResponse:
    if idempotency_key and idempotency_key in _idempotency:
        existing = repository.get_by_id(db, _idempotency[idempotency_key])
        if existing is not None:
            return present_one(db, existing)
    created = repository.create(db, data, author_id=author.id)
    if idempotency_key:
        _idempotency[idempotency_key] = created.id
    cache_clear()
    background_tasks.add_task(_notify_new_post, created.title)
    background_tasks.add_task(_publish_post_created, created.id)
    return present_one(db, created)


def update_post(db: Session, post_id: int, data: PostPatch, current_user: User) -> PostResponse:
    existing = get_post_or_404(db, post_id)
    _check_owner(existing, current_user)
    updated = repository.update(db, existing, data)
    cache_clear()
    return present_one(db, updated)


def delete_post(db: Session, post_id: int, current_user: User) -> None:
    existing = get_post_or_404(db, post_id)
    _check_owner(existing, current_user)
    repository.delete(db, existing)
    cache_clear()
