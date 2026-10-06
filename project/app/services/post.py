"""비즈니스 로직 계층. repositories(DB)와 routers(HTTP) 사이에서 규칙을 담당한다."""

import time
from typing import Optional

# BackgroundTasks: 응답을 보낸 "뒤에" 실행할 작업을 등록하는 FastAPI 도구
# HTTPException: 에러 상태코드와 메시지를 담아 던지면 FastAPI가 해당 에러 응답으로 바꿔준다
# status: HTTP 상태코드 상수 모음 (403 대신 status.HTTP_403_FORBIDDEN 처럼 읽기 쉽게 사용)
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User
# "import 모듈 as 별칭": repositories.post 모듈을 repository라는 이름으로 쓴다.
from app.repositories import post as repository
from app.schemas.post import PaginatedPosts, PostCreate


def get_post_or_404(db: Session, post_id: int) -> Post:
    post = repository.get_by_id(db, post_id)
    if post is None:
        # raise: 예외를 발생시켜 함수 실행을 즉시 중단 → 클라이언트에는 404 응답이 나간다.
        raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")
    return post


def list_posts_paginated(
    db: Session, published: Optional[bool], skip: int, limit: int
) -> PaginatedPosts:
    result = repository.list_all(db)
    # published가 None이면 "필터 없음"이므로 전체를 그대로 사용한다.
    if published is not None:
        # 리스트 컴프리헨션: 조건에 맞는 글만 골라 새 리스트를 만든다.
        result = [p for p in result if p.published == published]
    # 슬라이싱 [skip : skip+limit]: skip번째부터 limit개만 잘라낸다 (페이지 한 장 분량).
    page = result[skip : skip + limit]
    # total은 "잘라내기 전" 전체 개수 → 프론트엔드가 전체 페이지 수를 계산할 수 있다.
    return PaginatedPosts(items=page, total=len(result), skip=skip, limit=limit)


def _notify_new_post(title: str) -> None:
    """새 글 알림 발송을 흉내내는 느린 작업(예: 이메일/웹훅 호출)."""
    time.sleep(1)  # 1초 동안 멈춰 "오래 걸리는 작업"을 흉내낸다
    print(f"[background] notified about new post: {title}")


def create_post(
    db: Session, post: PostCreate, author: User, background_tasks: BackgroundTasks
) -> Post:
    created = repository.create(db, post, author_id=author.id)
    # 응답을 클라이언트로 보낸 뒤에 실행된다 — 클라이언트는 알림 발송을 기다리지 않는다.
    # add_task(실행할 함수, 그 함수에 넘길 인자...) 형태로 등록한다.
    background_tasks.add_task(_notify_new_post, created.title)
    return created


# 함수 이름 앞의 "_"(언더스코어): "이 모듈 내부에서만 쓰는 함수"라는 파이썬 관례 표시.
def _check_owner(post: Post, current_user: User) -> None:
    # 글의 작성자 id와 현재 로그인한 사용자 id가 다르면 → 403 Forbidden (권한 없음)
    #   401(인증 실패: 누군지 모름)과 구분: 403은 "누군지는 알지만 권한이 없음"
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 글만 수정/삭제할 수 있습니다.",
        )


def update_post(db: Session, post_id: int, data: PostCreate, current_user: User) -> Post:
    existing = get_post_or_404(db, post_id)  # 1) 글이 있는지 확인 (없으면 404)
    _check_owner(existing, current_user)  # 2) 내 글인지 확인 (아니면 403)
    return repository.update(db, existing, data)  # 3) 통과하면 실제로 수정


def delete_post(db: Session, post_id: int, current_user: User) -> None:
    existing = get_post_or_404(db, post_id)  # 존재 확인
    _check_owner(existing, current_user)  # 소유자 확인
    repository.delete(db, existing)  # 삭제
