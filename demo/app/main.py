from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import SessionLocal, engine
from app.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.routers import async_demo, auth, posts

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Demo")

# 프론트엔드(React/Vue 등 다른 origin)에서 이 API를 호출할 수 있도록 허용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 에러 응답 포맷을 한 곳에서 통일한다 (404/401/403 vs 422 vs 예상치 못한 500 모두 공통 처리).
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(posts.router)
app.include_router(auth.router)
app.include_router(async_demo.router)


def _seed_initial_posts() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(models.Post).count() == 0:
            db.add_all(
                [
                    models.Post(title="첫 번째 글", content="FastAPI 공부를 시작합니다.", published=True),
                    models.Post(title="비공개 초안", content="아직 다듬는 중입니다.", published=False),
                ]
            )
            db.commit()
    finally:
        db.close()


_seed_initial_posts()


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/hello")
def hello():
    return {"message": "board 라우트가 정상적으로 연결되었습니다."}


@app.get("/debug/boom")
def boom():
    """unhandled_exception_handler가 500을 어떻게 감싸는지 확인하기 위한 실습용 라우트."""
    raise ValueError("일부러 발생시킨 예외입니다.")
