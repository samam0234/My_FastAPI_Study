"""댓글 요청/응답 스키마."""

from datetime import datetime, timezone

from pydantic import Field, field_serializer

from app.schemas.common import APIModel
from app.schemas.post import Author, PageMeta


class CommentCreate(APIModel):
    body: str = Field(min_length=1, max_length=1000)


class CommentResponse(APIModel):
    id: int
    post_id: int
    body: str
    author: Author | None = None
    created_at: datetime

    @field_serializer("created_at")
    def _iso_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class CommentEnvelope(APIModel):
    data: CommentResponse


class CommentList(APIModel):
    data: list[CommentResponse]
    meta: PageMeta
