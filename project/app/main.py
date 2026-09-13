from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.posts.models import Post
from app.posts.router import router as posts_router
from app.users.router import router as auth_router

settings = get_settings()

# Post/User 모델은 각 도메인 router를 import하는 시점에 이미 Base.metadata에 등록된다.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mini Board API",
    description="FastAPI 커리큘럼(study0~study11)에서 배운 내용을 모아 만든 미니 게시판 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(posts_router)
app.include_router(auth_router)


def _seed_initial_posts() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Post).count() == 0:
            db.add_all(
                [
                    Post(title="첫 번째 글", content="Mini Board API에 오신 것을 환영합니다.", published=True),
                    Post(title="비공개 초안", content="아직 다듬는 중입니다.", published=False),
                ]
            )
            db.commit()
    finally:
        db.close()


_seed_initial_posts()


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Mini Board API"}
