from fastapi import HTTPException

from app.schemas import PostCreate, PostResponse

posts_db: list[PostResponse] = [
    PostResponse(id=1, title="첫 번째 글", content="FastAPI 공부를 시작합니다.", published=True),
    PostResponse(id=2, title="비공개 초안", content="아직 다듬는 중입니다.", published=False),
]
_next_post_id = 3


def list_posts() -> list[PostResponse]:
    return posts_db


def get_post_or_404(post_id: int) -> PostResponse:
    for post in posts_db:
        if post.id == post_id:
            return post
    raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")


def create_post(post: PostCreate) -> PostResponse:
    global _next_post_id
    new_post = PostResponse(id=_next_post_id, **post.model_dump())
    posts_db.append(new_post)
    _next_post_id += 1
    return new_post


def update_post(post_id: int, post: PostCreate) -> PostResponse:
    existing = get_post_or_404(post_id)
    existing.title = post.title
    existing.content = post.content
    existing.published = post.published
    return existing


def delete_post(post_id: int) -> None:
    existing = get_post_or_404(post_id)
    posts_db.remove(existing)
