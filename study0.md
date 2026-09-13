# study0. FastAPI 기초이론

> 이 저장소는 [Notion: FastAPI 학습 목표](https://app.notion.com/p/FastAPI-3d6d7dec5e2e810fb6f5fa9e53bcb9a2) 페이지를 기준으로 진행합니다.
> 최종 목표: **`/posts` CRUD + `/auth/login`**을 갖춘 API 서버를, 인메모리 → DB(SQLAlchemy) → JWT 인증 순서로 점진적으로 완성해보는 것.

## 1. FastAPI란?

FastAPI는 Python 타입힌트를 기반으로 하는 **API 전용(마이크로) 웹 프레임워크**입니다. Starlette(ASGI 웹 툴킷) 위에 Pydantic(데이터 검증 라이브러리)을 결합한 구조로, "빠르고(성능) + 빠르게 만들고(생산성) + 자동으로 문서화된다"는 세 가지를 핵심 가치로 내세웁니다.

- Netflix, Uber, Microsoft 등에서 내부 API 서버로 채택
- 함수 시그니처의 타입힌트만으로 요청 검증 + 응답 직렬화 + API 문서(Swagger UI)가 자동 생성됨
- Django/Flask와 달리 템플릿 엔진, Admin, ORM을 기본 내장하지 않음 — "API를 잘 만드는 것"에 집중

### Django와 고를 점 (Notion 요약)

| 구분 | Django | FastAPI |
|---|---|---|
| 성격 | 풀스택(all-in-one) | API 전용 마이크로 프레임워크 |
| ORM/Admin | 내장 | 없음(SQLAlchemy 등 직접 선택) |
| 데이터 검증 | Form/Serializer | Pydantic(타입힌트 기반) |
| 처리 방식 | 기본 동기(WSGI), ASGI는 선택 | 기본 비동기(ASGI) |
| API 문서 | DRF 도입 시 수동 설정 | 기본 내장(Swagger/ReDoc 자동 생성) |
| 적합한 상황 | 화면(템플릿)까지 한 번에 만들 때 | API 서버 성능·타입 안정성·문서화가 중요할 때 |

두 프레임워크는 "웹 요청을 받아 데이터를 처리하고 응답한다"는 본질은 같지만, FastAPI는 그 중 **API 계층만 최소한의 구조로 빠르게** 만들도록 설계되어 있습니다.

## 2. ASGI vs WSGI

- **WSGI(Web Server Gateway Interface)**: 요청 하나당 스레드 하나가 동기적으로 처리. Django/Flask가 기본으로 사용하던 방식.
- **ASGI(Asynchronous Server Gateway Interface)**: WSGI의 비동기 버전. 하나의 이벤트 루프가 여러 요청을 논블로킹으로 동시에 처리할 수 있어 WebSocket, 스트리밍, 대량 I/O 대기 작업에 유리.
- FastAPI는 처음부터 **ASGI 네이티브**로 설계되었고, 실행 서버로는 [uvicorn](https://www.uvicorn.org/)(또는 hypercorn)을 사용합니다.

```
[클라이언트]
   │ HTTP 요청
   ▼
[uvicorn] (ASGI 서버, 이벤트 루프 실행)
   ▼
[FastAPI app] : 경로(path)와 일치하는 라우트 함수 탐색
   │  - Pydantic으로 요청 바디/쿼리/경로 파라미터 검증
   │  - Depends()로 의존성(DB 세션, 인증 등) 주입
   │  - 라우트 함수 실행 (동기 또는 async def)
   ▼
[Pydantic 응답 모델] : 반환값을 JSON으로 직렬화
   ▼
[클라이언트] ◄── JSON 응답
```

## 3. 동기(sync)와 비동기(async)

- 라우트 함수는 `def`(동기) 또는 `async def`(비동기) 둘 다 정의할 수 있습니다.
- `async def`로 만든 라우트 안에서 `await`가 필요한 비동기 작업(비동기 DB 드라이버, 비동기 HTTP 호출 등)을 논블로킹으로 처리하면, 하나의 워커가 그 시간 동안 다른 요청도 처리할 수 있습니다.
- 반대로 `async def` 안에서 시간이 오래 걸리는 **동기(blocking) 코드**를 그냥 호출하면 이벤트 루프 전체가 멈춰버리는 역효과가 납니다. 이 경우 그냥 `def`로 만들면 FastAPI가 자동으로 별도 스레드풀에서 실행해줍니다.
- 즉, "무조건 async가 빠르다"가 아니라 **"내가 쓰는 라이브러리가 진짜 비동기를 지원하는가"**가 기준입니다. 자세한 실습은 study6(비동기 라우트)에서 다룹니다.

## 4. Pydantic: 타입힌트 기반 데이터 검증

FastAPI의 핵심 축 중 하나는 [Pydantic](https://docs.pydantic.dev/)입니다.

```python
from pydantic import BaseModel

class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = True
```

- 클래스 필드에 붙인 타입힌트(`str`, `bool` 등)를 런타임에 실제로 검증합니다. 타입이 안 맞으면 자동으로 422 에러 응답을 만들어줍니다.
- 요청 바디(Request Body)뿐 아니라 응답 모델(Response Model)로도 재사용되어, "어떤 데이터가 들어오고 나가는지"가 코드 자체로 문서화됩니다.
- Django의 Form/DRF Serializer, 그리고 일반적인 "DTO(Data Transfer Object)"에 대응하는 개념이라고 이해하면 됩니다.

## 5. 자동 API 문서화

FastAPI 앱을 실행하면 별도 설정 없이 아래 두 문서가 자동으로 생성됩니다.

- `/docs` : Swagger UI (브라우저에서 직접 요청을 날려볼 수 있는 대화형 문서)
- `/redoc` : ReDoc (읽기 좋은 정적 문서)

라우트 함수의 타입힌트, Pydantic 모델, docstring이 그대로 문서에 반영되므로 "코드가 곧 문서"에 가깝습니다.

## 6. 프로젝트 구성 요소 예고

Django의 `manage.py` / `settings.py` / `urls.py`에 대응하는 FastAPI 쪽 개념은 다음과 같습니다.

| Django | FastAPI | 역할 |
|---|---|---|
| `manage.py runserver` | `uvicorn main:app --reload` | 개발 서버 실행 |
| `urls.py` | `@app.get("/path")` 데코레이터, `APIRouter` | 경로 라우팅 |
| `views.py` | 라우트 함수(경로 오퍼레이션 함수) | 요청 처리 로직 |
| `models.py`(ORM) | SQLAlchemy/SQLModel 모델 (직접 선택) | DB 테이블 정의 |
| Form/Serializer | Pydantic `BaseModel` (schemas) | 요청/응답 데이터 검증 |
| 없음(직접 구현) | `Depends()` | 의존성 주입(DB 세션, 인증 등 공통 로직 재사용) |

Django처럼 "app" 단위로 강제 분리하지 않고, 프로젝트 구조는 자유롭게 설계합니다. 이 커리큘럼에서는 study3부터 `routers/`, `schemas.py`, `models.py`, `database.py`, `dependencies.py`로 구성된 구조를 사용합니다.

## 7. 이 커리큘럼의 로드맵

Notion 학습 목표를 아래와 같이 study 문서에 매핑했습니다.

| study 문서 | Notion 학습 목표 | 내용 |
|---|---|---|
| study0 | (선행 이론) | FastAPI 기초이론 |
| study1 | 설치/실행 | 설치, 실행 명령어, 첫 라우트 실습 |
| study2 | 경로, Path/Query, Pydantic 스키마 | `/posts` 인메모리 CRUD |
| study3 | 의존성 주입 | `Depends`, `APIRouter`로 프로젝트 구조화 |
| study4 | SQLAlchemy/SQLModel + MySQL | DB 연동, `/posts`를 DB 기반으로 전환 |
| study5 | (회원 도메인 준비) | User 모델, 비밀번호 해시, 회원가입 |
| study6 | 비동기 라우트 | `async def`, 블로킹 I/O, `BackgroundTasks` |
| study7 | JWT 인증 | `/auth/login`, `OAuth2PasswordBearer` |
| study8 | CORS, 예외 핸들러 | `CORSMiddleware`, 커스텀 예외 핸들러 |
| study9 | 테스트코드로 API 테스트 | pytest + `TestClient` |
| study10 | (마무리) | 설정 관리(`.env`), 페이지네이션/필터링 |
| studyFinal | (종합) | 지금까지 배운 것으로 미니 게시판 API 프로젝트 |

공통 스펙: **`/posts` CRUD + `/auth/login`**을 처음부터 끝까지 사용합니다. 저장소는 인메모리 리스트 → SQLAlchemy DB로, 인증은 없음 → JWT로 단계적으로 발전합니다.

## 8. 실습 프로젝트 구조 예고

- `demo/` : study1~study10 실습 내용이 단계별로 누적되는 FastAPI 프로젝트
- `project/` : studyFinal에서 만드는, 지금까지 배운 내용을 총정리한 완결된 미니 게시판 API

다음 문서(study1)부터 실제로 손을 움직여 프로젝트를 만들어봅니다.
