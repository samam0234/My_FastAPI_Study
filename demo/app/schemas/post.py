"""게시글 요청/응답 스키마. 목록은 data + meta 봉투를 쓴다."""

from datetime import datetime

from pydantic import Field, field_serializer

from app.schemas.common import APIModel


class Author(APIModel):
    id: int
    nickname: str


class PostCreate(APIModel):
    title: str = Field(min_length=1, max_length=200, examples=["첫 글"])
    body: str = Field(min_length=1, examples=["안녕하세요"])
    tags: list[str] = Field(default_factory=list, examples=[["intro"]])


class PostPatch(APIModel):
    """보낸 필드만 수정한다. 빼먹은 필드는 그대로 둔다."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None


class PostResponse(APIModel):
    id: int
    title: str
    body: str
    tags: list[str]
    author: Author | None = None
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _iso_utc(self, value: datetime) -> str:
        from datetime import timezone

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class PostEnvelope(APIModel):
    data: PostResponse


class PageMeta(APIModel):
    page: int
    limit: int
    total: int
    total_pages: int
    q: str = ""


class PostList(APIModel):
    data: list[PostResponse]
    meta: PageMeta
