"""앱 조립. APIRouter(prefix="/api") 아래에 게시글·회원·댓글을 모은다."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.errors import AppError
from app.exceptions import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware import RequestIdMiddleware
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.realtime import router as realtime_router
from app.routers import ai, auth, comment, integrations, post

logging.basicConfig(level=logging.INFO)
settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mini Board API",
    description="FastAPI 학습용 게시판 API. 공통 스펙 v1의 /api, data+meta, error 형식을 따른다.",
    version="1.0.0",
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

api = APIRouter(prefix="/api")
api.include_router(post.router)
api.include_router(auth.router)
api.include_router(comment.router)
api.include_router(integrations.router)
api.include_router(ai.router)
app.include_router(api)
app.include_router(realtime_router)


def _seed_initial_posts() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Post).count() == 0:
            now = datetime.now(timezone.utc)
            db.add_all(
                [
                    Post(
                        title="첫 번째 글",
                        body="Mini Board API에 오신 것을 환영합니다.",
                        tags="[]",
                        created_at=now,
                        updated_at=now,
                    ),
                    Post(
                        title="두 번째 글",
                        body="검색과 페이지네이션을 확인해 보세요.",
                        tags='["intro"]',
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )
            db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()


_seed_initial_posts()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Hello, FastAPI!", "docs": "/docs", "health": "/health"}


@app.get("/api-docs", include_in_schema=False)
def api_docs():
    """공통 스펙의 문서 경로. FastAPI 기본 Swagger는 /docs 에 있다."""
    return RedirectResponse(url="/docs")


# 모델 import가 린터에 지워지지 않도록 참조를 남긴다. create_all은 이 클래스들을 알아야 한다.
_MODELS = (User, Post, Comment)
