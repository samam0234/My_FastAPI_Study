# study1. 만드는 방법 및 명령어, 실습1

Notion 학습 목표 대응: **설치/실행**

이 문서부터는 실제로 동작하는 코드를 `demo/` 폴더에 만듭니다. `demo/`는 study1~study10에 걸쳐 계속 기능이 누적되는 하나의 FastAPI 프로젝트입니다.

## 1. 개발 환경 준비

```bash
# demo 프로젝트 전용 가상환경 생성
python -m venv demo/.venv

# 가상환경 활성화 (Windows PowerShell)
demo/.venv/Scripts/Activate.ps1

# FastAPI + ASGI 서버(uvicorn) 설치
pip install fastapi "uvicorn[standard]"

# 설치 확인
pip show fastapi uvicorn
```

- 가상환경(`venv`)은 프로젝트마다 독립적인 패키지 공간을 만들어줍니다. `demo/`와 `project/`는 각각 별도의 `.venv`를 가지며, 둘 다 Git에는 커밋하지 않습니다(`.gitignore` 참고).
- `uvicorn[standard]`로 설치하면 `watchfiles`(코드 변경 감지), `websockets` 등 개발 편의 패키지가 함께 설치됩니다.
- 설치한 패키지 목록은 `pip freeze > requirements.txt`로 기록해둡니다.

## 2. Django와의 명령어 대응

Django는 `django-admin startproject`로 정해진 폴더 구조를 생성해주지만, FastAPI는 그런 스캐폴딩 명령어가 없습니다. 그냥 Python 패키지/모듈 구조를 원하는 대로 만들면 됩니다. 이 커리큘럼에서는 study1에서 파일 하나(`main.py`)로 시작해서, study3부터 여러 모듈로 구조화합니다.

| Django | FastAPI |
|---|---|
| `django-admin startproject config .` | (없음 — `main.py` 파일 직접 작성) |
| `python manage.py startapp <이름>` | (없음 — 패키지/모듈을 직접 추가) |
| `python manage.py runserver` | `uvicorn main:app --reload` |
| `python manage.py migrate` | (study4에서 `Base.metadata.create_all()`로 대응) |

## 3. 첫 애플리케이션 작성

`demo/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="FastAPI Demo")


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/hello")
def hello():
    return {"message": "board 라우트가 정상적으로 연결되었습니다."}
```

- `FastAPI()` 인스턴스가 Django의 프로젝트 전체(설정 + 라우팅 테이블)에 해당하는 애플리케이션 객체입니다.
- `@app.get("/경로")` 데코레이터가 붙은 함수를 **경로 오퍼레이션 함수(path operation function)**라고 부릅니다. Django의 `views.py` 함수 + `urls.py` 매핑이 한 번에 이루어지는 셈입니다.
- 함수가 반환한 dict는 FastAPI가 자동으로 JSON으로 직렬화해서 응답합니다.

## 4. 실행 명령어

```bash
uvicorn main:app --reload --port 8001
```

- `main:app` : `main.py` 모듈 안의 `app` 객체를 실행하라는 의미 (`<모듈>:<변수명>`)
- `--reload` : 코드 변경 시 서버 자동 재시작 (개발용, 운영에서는 사용하지 않음)
- `--port` : 포트 지정 (기본값 8000)

## 5. 자주 쓰는 명령어 정리

| 명령어 | 설명 |
|---|---|
| `uvicorn main:app --reload` | 개발 서버 실행 (자동 재시작) |
| `uvicorn main:app --host 0.0.0.0 --port 8001` | 호스트/포트 지정 실행 |
| `pip freeze > requirements.txt` | 현재 설치된 패키지 목록 저장 |
| `pip install -r requirements.txt` | 저장된 패키지 목록으로 복원 |
| `pytest` | 테스트 실행 (study9에서 도입) |

## 6. 자동 생성되는 문서 확인

서버를 실행한 뒤 별도 설정 없이 아래 주소로 접속하면 API 문서를 바로 확인할 수 있습니다.

- `http://127.0.0.1:8001/docs` : Swagger UI
- `http://127.0.0.1:8001/redoc` : ReDoc

## 7. 실습1: 첫 라우트 띄우기 + 확인

`demo/` 폴더에서 진행한 실습 내용입니다.

1. `demo/.venv` 가상환경 생성 후 `fastapi`, `uvicorn[standard]` 설치
2. `demo/main.py`에 `/`, `/hello` 두 개의 라우트 작성
3. `uvicorn main:app --reload --port 8001`로 서버 실행
4. `curl`로 두 라우트와 `/docs`가 정상 응답하는지 확인
5. `pip freeze > requirements.txt`로 의존성 기록

### 확인 결과

```bash
$ curl http://127.0.0.1:8001/
{"message":"Hello, FastAPI!"}

$ curl http://127.0.0.1:8001/hello
{"message":"board 라우트가 정상적으로 연결되었습니다."}

$ curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/docs
200
```

정상적으로 응답이 오는 것을 확인했습니다. 다음 문서(study2)부터는 이 커리큘럼의 공통 스펙인 `/posts` CRUD를 Path/Query 파라미터와 Pydantic 스키마로 만들어봅니다.
