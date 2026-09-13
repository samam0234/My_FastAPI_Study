from typing import Optional

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel

app = FastAPI(title="FastAPI Demo")


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/hello")
def hello():
    return {"message": "board 라우트가 정상적으로 연결되었습니다."}


# ---------------------------------------------------------------------------
# study2: /posts 인메모리 CRUD
# ---------------------------------------------------------------------------


class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = True


class PostResponse(PostCreate):
    id: int


posts_db: list[PostResponse] = [
    PostResponse(id=1, title="첫 번째 글", content="FastAPI 공부를 시작합니다.", published=True),
    PostResponse(id=2, title="비공개 초안", content="아직 다듬는 중입니다.", published=False),
]
next_post_id = 3


def get_post_or_404(post_id: int) -> PostResponse:
    for post in posts_db:
        if post.id == post_id:
            return post
    raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")


@app.get("/posts", response_model=list[PostResponse])
def list_posts(
    published: Optional[bool] = Query(default=None, description="공개 여부로 필터링"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    result = posts_db
    if published is not None:
        result = [p for p in result if p.published == published]
    return result[skip : skip + limit]


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int = Path(..., gt=0, description="조회할 게시글 id")):
    return get_post_or_404(post_id)


@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate):
    global next_post_id
    new_post = PostResponse(id=next_post_id, **post.model_dump())
    posts_db.append(new_post)
    next_post_id += 1
    return new_post


@app.put("/posts/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: PostCreate):
    existing = get_post_or_404(post_id)
    existing.title = post.title
    existing.content = post.content
    existing.published = post.published
    return existing


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    existing = get_post_or_404(post_id)
    posts_db.remove(existing)
