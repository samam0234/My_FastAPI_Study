"""응답 필드 이름을 camelCase로 바꾸는 공통 스키마."""

from pydantic import BaseModel, ConfigDict


def to_camel(name: str) -> str:
    """snake_case 필드 이름을 camelCase 별칭으로 바꾼다.

    created_at -> createdAt, access_token -> accessToken.
    파이썬 코드는 snake_case를 유지하고, JSON만 공통 스펙의 camelCase를 쓴다.
    """
    head, *tail = name.split("_")
    return head + "".join(part.capitalize() for part in tail if part)


class APIModel(BaseModel):
    """alias_generator로 요청·응답 필드 이름을 camelCase로 맞춘다."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
