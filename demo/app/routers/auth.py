"""HTTP 계층. 요청을 파싱해 services에 넘기고, services의 결과를 그대로 응답한다."""

# APIRouter: 라우트를 묶어 관리하는 "미니 앱" / Depends: 의존성 주입 표시
from fastapi import APIRouter, Depends

# OAuth2PasswordRequestForm: 로그인 폼(username, password)을 form-data로 받는 표준 의존성
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services import user as service

# prefix="/auth": 이 라우터의 모든 경로 앞에 /auth가 붙는다 (/auth/register, /auth/login)
# tags=["auth"]: /docs 화면에서 "auth" 그룹으로 묶어 보여준다
router = APIRouter(prefix="/auth", tags=["auth"])


# @router.post(...): POST 방식 요청을 이 함수에 연결하는 데코레이터
# response_model=UserResponse: 응답을 이 스키마 모양으로 걸러낸다 (비밀번호 해시가 새어나가지 않음)
# status_code=201: 성공 시 기본 200 대신 201(Created)을 반환한다
@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # user: UserCreate → 요청 JSON 본문이 자동으로 검증·변환되어 들어온다
    # db: Depends(get_db) → 요청마다 DB 세션을 자동 주입받는다
    return service.register_user(db, user)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form_data: JSON이 아니라 form-data(username, password)로 받는다 → /docs의 Authorize 버튼과 호환
    return service.authenticate(db, form_data.username, form_data.password)
