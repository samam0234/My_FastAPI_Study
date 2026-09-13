from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.config import get_settings
from app.database import SessionLocal, engine
from app.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.routers import auth, posts

settings = get_settings()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mini Board API",
    description="FastAPI 커리큘럼(study0~study10)에서 배운 내용을 모아 만든 미니 게시판 API",
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

app.include_router(posts.router)
app.include_router(auth.router)


def _seed_initial_posts() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(models.Post).count() == 0:
            db.add_all(
                [
                    models.Post(title="첫 번째 글", content="Mini Board API에 오신 것을 환영합니다.", published=True),
                    models.Post(title="비공개 초안", content="아직 다듬는 중입니다.", published=False),
                ]
            )
            db.commit()
    finally:
        db.close()


_seed_initial_posts()


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Mini Board API"}
