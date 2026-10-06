# ─────────────────────────────────────────────────────────────
# main.py : 애플리케이션의 진입점(앱 조립 파일)
#   FastAPI 앱 생성 → 테이블 생성 → CORS/예외 핸들러 등록 → 라우터 연결 → 초기 데이터 주입
#   실행: uvicorn app.main:app --reload   (app 패키지의 main.py 안의 app 변수를 실행한다는 뜻)
# ─────────────────────────────────────────────────────────────
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
# CORSMiddleware: 다른 출처(origin)의 프론트엔드가 API를 호출할 수 있도록 CORS 헤더를 붙여주는 미들웨어
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.models.post import Post
from app.routers import auth, post

settings = get_settings()

# Post/User 모델은 각 라우터 모듈을 import하는 시점에 이미 Base.metadata에 등록된다.
# create_all: Base를 상속한 모든 모델에 해당하는 테이블을 DB에 만든다 (이미 있으면 건너뜀).
Base.metadata.create_all(bind=engine)

# FastAPI 앱 객체 생성. 아래 세 값은 /docs(Swagger UI) 상단의 제목·설명·버전으로 표시된다.
app = FastAPI(
    title="Mini Board API",
    description="FastAPI 커리큘럼(study0~study11)에서 배운 내용을 모아 만든 미니 게시판 API",
    version="1.0.0",
)

# 미들웨어: 모든 요청/응답이 라우트 앞뒤에서 반드시 거쳐가는 공통 처리 계층.
# CORS: 다른 origin(예: React 개발 서버)에서 이 API를 호출할 수 있도록 허용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 허용할 프론트엔드 주소 목록
    allow_credentials=True,  # 쿠키/인증 헤더를 포함한 요청도 허용
    allow_methods=["*"],  # 모든 HTTP 메서드(GET/POST/PUT/DELETE...) 허용
    allow_headers=["*"],  # 모든 요청 헤더 허용
)

# 에러 응답 포맷을 한 곳에서 통일한다.
# add_exception_handler(예외 클래스, 처리 함수): 해당 예외가 발생하면 그 함수가 응답을 만든다.
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # 404/401/403 등
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # 422 검증 실패
app.add_exception_handler(Exception, unhandled_exception_handler)  # 예상 못한 500

# include_router: 다른 파일에 정의한 라우터를 앱에 연결한다 (연결해야 실제로 URL이 활성화됨).
app.include_router(post.router)
app.include_router(auth.router)


# 서버가 시작될 때 샘플 글 2개를 넣어주는 시드(seed) 함수. 앞의 "_"는 내부용 함수 표시.
def _seed_initial_posts() -> None:
    # 라우트 밖에서는 Depends(get_db)를 쓸 수 없으므로 세션을 직접 만들고 직접 닫는다.
    db: Session = SessionLocal()
    try:
        # 글이 하나도 없을 때만 넣는다 → 서버를 재시작해도 중복 삽입되지 않는다.
        if db.query(Post).count() == 0:
            db.add_all(  # add_all: 여러 객체를 한 번에 저장 예정으로 등록
                [
                    Post(title="첫 번째 글", content="Mini Board API에 오신 것을 환영합니다.", published=True),
                    Post(title="비공개 초안", content="아직 다듬는 중입니다.", published=False),
                ]
            )
            db.commit()  # 확정
    finally:
        db.close()  # 예외가 나도 반드시 세션을 닫는다


_seed_initial_posts()  # 모듈이 import되는(=서버 시작) 시점에 한 번 실행


# tags=["health"]: /docs에서 "health" 그룹으로 표시. 서버가 살아있는지 확인하는 헬스체크용 엔드포인트.
@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Mini Board API"}
