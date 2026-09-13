# study6. 고급 기술 구현 1 — 비동기 라우트

Notion 학습 목표 대응: **비동기 라우트**

study0에서 "async가 무조건 빠른 건 아니다"라고 예고했던 내용을 이번 문서에서 실제로 재현해봅니다. `app/routers/async_demo.py`에 세 가지 라우트를 만들고, 동시에 여러 요청을 보내 걸리는 시간을 직접 비교했습니다.

## 1. 세 가지 패턴

```python
@router.get("/bad-async")
async def bad_async():
    time.sleep(2)          # async def 안에서 blocking 코드를 직접 호출 (나쁜 예)
    return {"done": "bad-async"}


@router.get("/good-async")
async def good_async():
    await asyncio.sleep(2)  # 진짜 비동기 I/O로 대기 (좋은 예)
    return {"done": "good-async"}


@router.get("/sync-def")
def sync_def():
    time.sleep(2)           # 일반 def — FastAPI가 스레드풀에서 자동 실행
    return {"done": "sync-def"}
```

- **`bad-async`**: `async def`로 선언했지만 내부에서 `time.sleep()`(동기/블로킹 함수)을 직접 호출했습니다. `await`가 없으므로 이 2초 동안 **이벤트 루프 자체가 멈춰서** 다른 요청을 전혀 처리하지 못합니다.
- **`good-async`**: `await asyncio.sleep()`으로 "진짜" 비동기 대기를 합니다. 대기하는 동안 이벤트 루프가 다른 요청을 계속 처리할 수 있습니다.
- **`sync-def`**: `async` 없이 그냥 `def`로 선언했습니다. FastAPI(Starlette)는 `async def`가 아닌 라우트를 만나면 **자동으로 별도 스레드풀에서 실행**해줘서, 내부에 블로킹 코드가 있어도 메인 이벤트 루프는 막히지 않습니다.

## 2. 동시 요청 3개로 실측 비교

```bash
uvicorn app.main:app --reload --port 8001
```

동일하게 "2초 걸리는 작업"이지만, 요청 3개를 **동시에** 보냈을 때 전체 소요 시간이 다릅니다.

```bash
$ time ( curl -s http://127.0.0.1:8001/async-demo/bad-async & \
         curl -s http://127.0.0.1:8001/async-demo/bad-async & \
         curl -s http://127.0.0.1:8001/async-demo/bad-async & wait )
real    0m6.077s   # 2초 x 3 = 순서대로 처리됨 (이벤트 루프가 막혀서 직렬화)

$ time ( curl -s http://127.0.0.1:8001/async-demo/good-async & \
         curl -s http://127.0.0.1:8001/async-demo/good-async & \
         curl -s http://127.0.0.1:8001/async-demo/good-async & wait )
real    0m2.064s   # 3개가 동시에 처리됨

$ time ( curl -s http://127.0.0.1:8001/async-demo/sync-def & \
         curl -s http://127.0.0.1:8001/async-demo/sync-def & \
         curl -s http://127.0.0.1:8001/async-demo/sync-def & wait )
real    0m2.067s   # 스레드풀 덕분에 역시 동시에 처리됨
```

`bad-async`만 3배(6초)가 걸렸고, `good-async`와 `sync-def`는 둘 다 2초 만에 끝났습니다. **"`async def`로 선언했다"는 사실 자체가 아니라, "그 안에서 진짜 비동기 I/O를 쓰는가"가 성능을 가른다**는 것을 직접 확인했습니다. 참고로 `sync-def` 방식은 스레드풀 크기만큼만 동시 처리가 가능하다는 한계가 있어(기본값은 넉넉하지만 무한하지 않음), 대량 트래픽에서는 `good-async`처럼 진짜 비동기 라이브러리(비동기 DB 드라이버, `httpx.AsyncClient` 등)를 쓰는 쪽이 더 유리합니다.

## 3. `BackgroundTasks`: 응답 이후에 실행할 작업

요청-응답과 무관하게 "응답은 먼저 보내고, 뒤에서 마저 처리해도 되는 일"(알림 발송, 로그 적재 등)은 `BackgroundTasks`로 분리합니다. `app/routers/posts.py`의 `create_post`에 추가했습니다.

```python
def notify_new_post(title: str) -> None:
    """새 글 알림 발송을 흉내내는 느린 작업(예: 이메일/웹훅 호출)."""
    time.sleep(1)
    print(f"[background] notified about new post: {title}")


@router.post("", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    created = store.create_post(db, post)
    background_tasks.add_task(notify_new_post, created.title)
    return created
```

- 라우트 함수 인자에 `background_tasks: BackgroundTasks`를 선언하기만 하면 FastAPI가 알아서 주입해줍니다.
- `background_tasks.add_task(함수, *인자)`로 등록해두면, **응답을 클라이언트에게 보낸 뒤에** 해당 함수가 실행됩니다. 클라이언트는 `notify_new_post`의 1초 대기를 전혀 기다리지 않습니다.

### 실측 결과

```bash
$ time curl -s -X POST http://127.0.0.1:8001/posts \
    -H "Content-Type: application/json" \
    -d '{"title":"study6 background task","content":"testing BackgroundTasks","published":true}'
{"title":"study6 background task","content":"testing BackgroundTasks","published":true,"id":3}
real    0m0.158s
```

응답은 0.16초 만에 왔지만, 서버 로그에는 응답이 나간 뒤 시차를 두고 백그라운드 작업이 찍혔습니다.

```
INFO:     127.0.0.1:55398 - "POST /posts HTTP/1.1" 201 Created
[background] notified about new post: study6 background task
[dependency] request handled in 1126.84ms
```

> **참고**: `[dependency] request handled in ...`(study3에서 만든 `log_request_time` 의존성)의 측정 시간이 응답 자체(0.16초)보다 훨씬 길게(1126ms) 찍히는 것도 확인했습니다. `yield`를 쓰는 의존성의 "정리(cleanup)" 코드는 응답이 나간 뒤 실행되는 백그라운드 태스크가 **모두 끝난 다음**에 실행되기 때문입니다. 즉 클라이언트 입장의 응답 속도와, 요청 하나가 서버 안에서 완전히 마무리되는 시점은 다를 수 있다는 것을 실측으로 확인한 셈입니다.

다음 문서(study7)에서는 이 커리큘럼의 핵심 과제인 **JWT 인증**을 구현해 `/auth/login`을 완성하고, `/posts` 작성 시 로그인한 사용자만 허용하도록 만듭니다.
