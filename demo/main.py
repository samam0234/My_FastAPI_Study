from fastapi import FastAPI

app = FastAPI(title="FastAPI Demo")


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/hello")
def hello():
    return {"message": "board 라우트가 정상적으로 연결되었습니다."}
