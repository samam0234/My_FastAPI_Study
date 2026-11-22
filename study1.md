# study1. Hello World와 기본 문법

## ① 목표

첫 JSON 응답을 띄우고, 함수가 경로가 되는 방식과 자동 새로고침을 확인한다.

## ② 📖 이론

### 왜 쓰는지

FastAPI에는 HTML 템플릿이 기본이 아니다. 화면 대신 JSON을 돌려주고, 그 JSON을 나중에 프론트가 그린다. 첫 응답은 "서버가 내 함수를 실행했다"는 증거다.

### 핵심 개념

- `@app.get("/health")`: GET 요청이 이 주소로 오면 바로 아래 함수를 실행한다.
- 함수가 `dict`를 반환하면 FastAPI가 JSON으로 바꾼다.
- 타입 힌트 `-> dict`는 사람을 위한 설명이고, 응답 모델을 붙이면 문서와 검증에도 쓰인다.
- `--reload`는 저장할 때마다 프로세스를 다시 시작한다.

### 비유

경로는 초인종 버튼이다. 버튼마다 다른 사람이 나와 다른 쪽지를 건넨다. `/health` 쪽지에는 "살아 있다"만 적혀 있다.

## ③ 🛠️ 실기

`demo/app/main.py`에서 첫 화면 역할을 하는 경로는 세 개다. 앱 생성과 이 경로만 떼어 보면 다음과 같다.

```python
from fastapi import FastAPI

app = FastAPI(title="FastAPI Demo", version="1.0.0")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!", "docs": "/docs", "health": "/health"}

@app.get("/hello", tags=["hello"])
def hello():
    return {"message": "board 라우트가 정상적으로 연결되었습니다."}
```

줄별 설명:

1. `FastAPI` 클래스를 가져온다. 이 클래스의 인스턴스가 곧 웹 애플리케이션이다.
2. 빈 줄.
3. `app`이라는 이름의 앱을 만든다. `title`과 `version`은 `/docs` 화면에 나온다.
4. 빈 줄.
5. 데코레이터. `/health`로 들어오는 GET을 다음 함수에 연결하고 문서에서 health 그룹으로 묶는다.
6. 함수 이름 `health_check`는 URL이 아니다. URL은 데코레이터의 문자열이다.
7. 딕셔너리를 반환한다. 키 `status`, 값 `ok`. 공통 스펙의 건강 체크 본문과 같다.
8. 빈 줄.
9. 루트 `/` GET.
10. 함수 정의.
11. 사람이 브라우저로 루트를 열었을 때의 안내 메시지. 문서와 건강 체크 주소를 같이 알려 준다.
12. 빈 줄.
13. `/hello` GET. 라우터를 붙이기 전에 "내 앱이 응답하는가"를 보는 연습 경로다.
14. 함수 정의.
15. 연결 확인용 문장. 이 문장이 보이면 프로세스가 이 파일을 읽고 있다는 뜻이다.

실행:

```powershell
cd demo
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001
```

확인할 주소:

- http://127.0.0.1:8001/
- http://127.0.0.1:8001/hello
- http://127.0.0.1:8001/health
- http://127.0.0.1:8001/docs

`/docs`는 Swagger UI다. 경로 목록이 비어 있지 않고 `health`, `hello`가 보이면 앱 객체가 문서를 만든 것이다.

브라우저 개발자 도구(F12) → Network → `/health`를 새로고침한다.

- Method는 GET
- Status는 200
- Response는 `{"status":"ok"}`
- Content-Type은 `application/json`

`hello()`의 문자열을 조금 바꾼 뒤 저장한다. 터미널에 `Reloading...`이 보이고, 새로고침한 응답 본문이 바뀌면 자동 새로고침이 동작한 것이다. 브라우저 캐시가 의심되면 Network에서 Disable cache를 켠다.

템플릿 표현은 이 프레임워크의 기본 응답에 없다. 문자열 포매팅이 필요하면 파이썬 f-string으로 JSON 값을 만든다.

```python
def hello_name(name: str = "FastAPI"):
    return {"message": f"Hello, {name}"}
```

`f"..."` 안의 `{name}`이 템플릿에서 변수 자리와 같은 역할이다. HTML로 뿌리지 않으므로 XSS 문맥은 프론트 쪽 이야기다.

## ④ 🔗 연동 포인트

`/health`는 앞에 `/api`를 붙이지 않는다. 이후 게시글과 회원은 `/api` 아래로 모으고, 살아 있는지만 보는 경로는 루트 근처에 둔다. 배포 뒤에도 이 주소로 프로세스가 응답하는지 확인한다. 프론트는 이 JSON을 화면에 그리지 않고, 개발 중에는 Network 탭으로 상태 코드와 본문만 보면 된다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `Could not import module "app.main"` | 실행 위치가 `demo`가 아님 | `cd demo` 후 다시 uvicorn |
| 새로고침해도 옛 문장 | reload가 꺼져 있거나 다른 포트 | 명령에 `--reload`가 있는지, 포트가 8001인지 확인 |
| `/docs`가 열리지 않음 | 서버가 죽음 | 터미널의 Traceback을 먼저 읽는다 |
| 브라우저가 HTML 오류 페이지 | 주소가 백엔드가 아님 | `127.0.0.1:8001`인지 확인. 3000은 프론트 포트다 |

## ⑥ 직접 해보기

1. `/hello` 문장을 바꾸고 저장한 뒤, Network 탭에서 응답이 바뀌었는지 확인한다.
2. Swagger의 hello 항목에서 Try it out → Execute를 눌러 같은 JSON이 나오는지 본다.
3. 없는 주소 `/no-such`를 연다. 상태 코드가 404이고 본문에 `error.code`가 있는지만 메모한다. 형식은 study4에서 맞춘다.

## ⑦ ☐ 체크리스트

- [ ] `GET /`와 `GET /hello`가 JSON을 반환한다.
- [ ] `GET /health`가 `{"status":"ok"}`이다.
- [ ] `--reload`로 저장 즉시 서버가 다시 뜬다.
- [ ] 개발자 도구 Network에서 상태 코드와 Content-Type을 읽었다.
- [ ] `/docs`에서 경로 목록을 열었다.

## ⑧ 다음 단계

한 파일의 함수에서 응답이 나왔으면, study2에서 그 함수를 라우터·서비스로 나누고 의존성 주입으로 서로 부르게 한다.
