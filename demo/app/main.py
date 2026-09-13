from sqlalchemy.orm import Session

from fastapi import FastAPI

from app import models
from app.database import SessionLocal, engine
from app.routers import auth, posts

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Demo")

app.include_router(posts.router)
app.include_router(auth.router)


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
