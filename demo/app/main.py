from fastapi import FastAPI

from app.routers import posts

app = FastAPI(title="FastAPI Demo")

app.include_router(posts.router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/hello")
def hello():
    return {"message": "board 라우트가 정상적으로 연결되었습니다."}
