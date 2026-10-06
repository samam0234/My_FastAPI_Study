"""HTTP 계층. 요청을 파싱해 services에 넘기고, services의 결과를 그대로 응답한다."""

from typing import Optional

# BackgroundTasks: 응답 후 실행할 작업 등록용 / Path: 경로 파라미터 검증 / Query: 쿼리 파라미터 검증
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import Pagination, log_request_time
from app.models.user import User
from app.schemas.post import PaginatedPosts, PostCreate, PostResponse
from app.services import post as service
from app.services.user import get_current_user

router = APIRouter(
    prefix="/posts",  # 모든 경로 앞에 /posts 가 붙는다
    tags=["posts"],  # /docs에서 "posts" 그룹으로 표시
    # 라우터 단위 의존성: 이 라우터의 "모든" 라우트가 실행될 때 log_request_time이 함께 실행된다.
    dependencies=[Depends(log_request_time)],
)


# GET /posts : 글 목록 조회 (누구나 접근 가능)
@router.get("", response_model=PaginatedPosts)
def list_posts(
    # 쿼리스트링 ?published=true 로 받는다. 기본값 None → 필터 없이 전체 조회.
    published: Optional[bool] = Query(default=None, description="공개 여부로 필터링"),
    # ?skip=0&limit=10 을 클래스 의존성으로 한 번에 받는다.
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
):
    return service.list_posts_paginated(db, published, pagination.skip, pagination.limit)


# GET /posts/{post_id} : 글 한 건 조회. 경로의 {post_id} 값이 같은 이름의 매개변수로 들어온다.
@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    # Path(...): "..."은 필수라는 뜻 / gt=0: 0보다 커야 함(greater than) / description: /docs 설명
    post_id: int = Path(..., gt=0, description="조회할 게시글 id"),
    db: Session = Depends(get_db),
):
    return service.get_post_or_404(db, post_id)


# POST /posts : 글 작성 (로그인 필요)
@router.post("", response_model=PostResponse, status_code=201)
def create_post(
    post: PostCreate,  # 요청 JSON 본문 (Request Body)
    background_tasks: BackgroundTasks,  # FastAPI가 자동으로 만들어 넣어주는 백그라운드 작업 등록기
    db: Session = Depends(get_db),
    # get_current_user에 의존 → 토큰이 없거나 잘못되면 여기까지 오기 전에 401로 차단된다.
    current_user: User = Depends(get_current_user),
):
    return service.create_post(db, post, current_user, background_tasks)


# PUT /posts/{post_id} : 글 수정 (로그인 + 본인 글만)
@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,  # 경로 파라미터
    post: PostCreate,  # 본문: 수정할 내용
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_post(db, post_id, post, current_user)


# DELETE /posts/{post_id} : 글 삭제 (로그인 + 본인 글만)
# status_code=204: "성공했고 돌려줄 본문은 없음"(No Content)
@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_post(db, post_id, current_user)
