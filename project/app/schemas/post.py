# ─────────────────────────────────────────────────────────────
# schemas/post.py : 게시글 요청/응답 데이터의 "모양"을 정의하는 Pydantic 스키마
#   - ORM 모델(models)은 DB 테이블용, 스키마(schemas)는 API 입출력용으로 역할이 다르다.
#   - Pydantic이 타입 검증·변환을 자동으로 해주고 /docs 문서도 자동 생성해 준다.
# ─────────────────────────────────────────────────────────────
from typing import Optional

# BaseModel: 모든 Pydantic 스키마의 부모 클래스 / ConfigDict: 스키마 동작 옵션 지정
from pydantic import BaseModel, ConfigDict


# 글 "생성/수정" 요청 본문(Request Body)의 형태
class PostCreate(BaseModel):
    title: str  # 필수 필드 (기본값 없음 → 없으면 422 에러)
    content: str  # 필수 필드
    published: bool = True  # 선택 필드 (안 보내면 True)


# 글 "응답"의 형태: PostCreate의 필드를 모두 물려받고 id, author_id를 추가한다.
class PostResponse(PostCreate):
    # from_attributes=True: dict가 아니라 ORM 객체(post.title 처럼 속성 접근)에서도
    # 값을 읽어 스키마로 변환할 수 있게 한다. (SQLAlchemy 객체를 그대로 반환하려면 필요)
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: Optional[int] = None  # 작성자가 없을 수도 있으므로 None 허용


# 목록 조회 응답: 페이지네이션 정보를 함께 내려준다.
class PaginatedPosts(BaseModel):
    items: list[PostResponse]  # 현재 페이지의 글 목록
    total: int  # 조건에 맞는 전체 글 개수
    skip: int  # 건너뛴 개수 (요청 값 그대로)
    limit: int  # 한 페이지 크기 (요청 값 그대로)
