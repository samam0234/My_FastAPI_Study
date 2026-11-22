"""demo 앱 조립. 기초 구간 라우트(/hello, /debug/boom, /async-demo)를 함께 둔다."""

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
from app.routers import async_demo, auth, comment, post

logging.basicConfig(level=logging.INFO)
settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Demo",
    description="study0~study10과 midpoint에서 쌓는 게시판 API.",
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
app.include_router(api)
app.include_router(async_demo.router)


def _seed_initial_posts() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Post).count() == 0:
            now = datetime.now(timezone.utc)
            db.add_all(
                [
                    Post(
                        title="첫 번째 글",
                        body="FastAPI 공부를 시작합니다.",
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


@app.get("/hello", tags=["hello"])
def hello():
    return {"message": "board 라우트가 정상적으로 연결되었습니다."}


@app.get("/debug/boom", tags=["debug"])
def boom():
    """처리하지 않은 예외가 500 일반 메시지로 바뀌는지 보는 실습용 경로."""
    raise ValueError("일부러 발생시킨 예외입니다.")


@app.get("/api-docs", include_in_schema=False)
def api_docs():
    return RedirectResponse(url="/docs")


_MODELS = (User, Post, Comment)
