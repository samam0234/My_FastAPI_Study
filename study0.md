# study0. 환경 설정

## ① 목표

FastAPI를 실행할 파이썬 환경을 만들고, 빈 프로젝트가 개발 서버로 뜨는 것까지 확인한다.

## ② 📖 이론

### 왜 쓰는지

FastAPI는 타입 힌트를 읽어 요청을 검증하고, Swagger 문서를 자동으로 만든다. 그 앞에서 필요한 것은 격리된 파이썬 환경이다. 전역 파이썬에 패키지를 깔면 다른 프로젝트와 버전이 섞인다.

### 핵심 개념

- **가상환경**: 이 폴더만 쓰는 파이썬과 pip.
- **ASGI**: uvicorn이 FastAPI 앱을 받아 HTTP 요청을 넘기는 비동기 서버 규격.
- **의존성 파일**: `requirements.txt`에 버전을 고정해 다른 컴퓨터에서도 같은 패키지를 깔 수 있게 한다.
- **환경 변수**: DB 주소와 비밀키는 코드 밖 `.env`에 둔다.

### 비유

가상환경은 실험실 칸막이다. 이 칸의 시약(패키지)이 옆 칸으로 흘러가지 않는다. `.env`는 칸 밖에 둔 열쇠 서랍이다.

## ③ 🛠️ 실기

이 저장소는 이미 `demo/`(기초·midpoint)와 `project/`(심화·final)로 나뉘어 있다. 새 연습을 처음부터 만들 때는 `demo`와 같은 순서를 따른다.

### 1) 버전 확인

```powershell
python --version
pip --version
```

학습 당시 앱이 기대하는 주요 버전은 `requirements.txt`에 고정되어 있다.

- Python 3.10 이상 (이 저장소 가상환경은 3.10, CI는 3.12)
- fastapi 0.141.1
- pydantic 2.13.5
- sqlalchemy 2.0.52
- uvicorn 0.52.4

설치된 뒤에 확인한다.

```powershell
pip show fastapi
python -c "import fastapi; print(fastapi.__version__)"
uvicorn --version
```

### 2) 가상환경과 설치

```powershell
cd demo
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`Activate.ps1`이 막히면 PowerShell에서 현재 사용자만 스크립트를 허용한 뒤 다시 켠다.

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 3) 프로젝트 폴더

```text
FastApi/
├── study0.md ~ study10.md
├── studyMidpoint.md
├── study11.md ~ study18.md
├── studyFinal.md
├── demo/                  # 기초 실습 앱, 포트 8001
│   ├── app/
│   ├── tests/
│   ├── frontend/
│   ├── requirements.txt
│   └── .env.example
└── project/               # 심화까지 포함한 게시판, 포트 8000
    ├── app/
    ├── tests/
    ├── frontend/
    ├── examples/
    ├── Dockerfile
    └── docker-compose.yml
```

`app/` 안은 나중에 이렇게 나눈다. study0에서는 이름만 기억한다.

- `main.py`: 앱을 조립한다.
- `routers/`: URL과 함수를 연결한다.
- `schemas/`: 요청·응답 모양.
- `models/`: DB 테이블.
- `repositories/`: SQL만.
- `services/`: 규칙(404, 403, 해시).

### 4) 환경 변수 파일

```powershell
copy .env.example .env
```

`.env.example`의 앞부분은 다음이다.

```env
DATABASE_URL=sqlite:///./demo.db
SECRET_KEY=change-me-to-a-long-random-value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

줄별 의미:

1. `DATABASE_URL`: SQLAlchemy 접속 문자열. 기본은 현재 폴더의 SQLite 파일.
2. `SECRET_KEY`: JWT 서명 키. 학습용 값을 운영에 그대로 두면 안 된다.
3. `ALGORITHM`: 서명 알고리즘. 이 앱은 HS256.
4. `ACCESS_TOKEN_EXPIRE_MINUTES`: 로그인 토큰이 살아있는 시간(분).

`.env`는 `.gitignore`에 있다. example만 커밋한다.

### 5) Git

저장소가 이미 있다면 `git status`만 확인한다. 새 폴더에서 시작할 때는 다음이다.

```powershell
git init
```

루트 `.gitignore`는 가상환경, 바이트코드, SQLite, `.env`, 업로드 폴더를 제외한다.

```gitignore
.venv/
__pycache__/
*.db
.env
uploads/
backups/
```

### 6) 개발 서버

아직 라우트를 만들기 전이라도, 이 저장소의 `demo`는 바로 실행할 수 있다.

```powershell
uvicorn app.main:app --reload --port 8001
```

- `app.main:app`: `app/main.py` 안의 `app` 객체.
- `--reload`: 코드가 저장되면 서버가 다시 뜬다.

브라우저에서 `http://127.0.0.1:8001/health` 를 연다. `{"status":"ok"}` 가 보이면 환경은 준비된 것이다. 종료는 `Ctrl+C`.

### 7) 에디터 확장

Cursor 또는 VS Code에서 다음을 켠다.

- Python (인터프리터를 `demo/.venv`로 선택)
- Pylance (타입 힌트 경고)

인터프리터를 가상환경으로 고르지 않으면 import 오류가 에디터에만 보인다.

### 8) 이 프레임워크에서 반복되는 말

| 용어 | 의미 |
| --- | --- |
| 경로(route) | URL과 함수의 연결 |
| 스키마 | 들어오고 나가는 JSON의 모양 |
| 의존성 | 요청마다 FastAPI가 대신 만들어 넣어 주는 값 |
| ORM | 테이블 행을 파이썬 객체로 다루는 층 |
| 상태 코드 | 200 성공, 201 생성, 204 본문 없음, 400 잘못된 입력, 401 로그인 필요, 403 권한 없음, 404 없음, 500 서버 오류 |

## ④ 🔗 연동 포인트

이 단계의 결과물은 다음 단계가 올라탈 바닥이다. Git 저장소가 있으면 study 문서와 코드를 같이 커밋할 수 있다. `.env`의 `DATABASE_URL`은 study6에서 MySQL 주소로 바꾸고, study11에서 PostgreSQL 주소로 바꾼다. 코드는 그 문자열만 읽는다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `python`을 찾을 수 없음 | PATH에 파이썬이 없음 | python.org 설치 때 PATH를 켜거나 `py -3` 사용 |
| Activate.ps1 실행 정책 오류 | PowerShell이 스크립트를 막음 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `No module named fastapi` | 가상환경을 안 켰거나 설치 전 | activate 후 `pip install -r requirements.txt` |
| 포트가 이미 사용 중 | 예전 uvicorn이 살아 있음 | 그 터미널에서 Ctrl+C 하거나 `--port 8002` |
| 에디터만 import 오류 | 인터프리터가 전역 파이썬 | 인터프리터를 `.venv`로 변경 |

## ⑥ 직접 해보기

1. `demo`에서 가상환경을 켜고 `pip show fastapi`의 버전이 `requirements.txt`와 같은지 확인한다.
2. `.env.example`을 `.env`로 복사한 뒤 `SECRET_KEY`만 다른 문장으로 바꾼다. `.env`가 `git status`에 안 나와야 한다.
3. `uvicorn app.main:app --reload --port 8001` 로 띄우고 `/health`를 새로고침한다. 코드를 저장하면 터미널에 reload가 찍히는지 본다.

## ⑦ ☐ 체크리스트

- [ ] Python 버전과 `pip show fastapi`를 확인했다.
- [ ] `demo/.venv`를 만들고 `requirements.txt`를 설치했다.
- [ ] 폴더 구조에서 `app`, `tests`, `frontend`의 역할을 말할 수 있다.
- [ ] `.env`를 만들었고 Git에는 올라가지 않는 것을 확인했다.
- [ ] `uvicorn ... --reload`로 `/health`가 `{"status":"ok"}`를 반환한다.
- [ ] 에디터 인터프리터가 가상환경을 가리킨다.

## ⑧ 다음 단계

환경이 켜지면 study1에서 첫 JSON 응답과 자동 새로고침, 브라우저 개발자 도구로 그 응답을 읽는다.
