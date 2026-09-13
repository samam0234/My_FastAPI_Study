from typing import Optional

from pydantic import BaseModel, ConfigDict


class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = True


class PostResponse(PostCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: Optional[int] = None


class PaginatedPosts(BaseModel):
    items: list[PostResponse]
    total: int
    skip: int
    limit: int
