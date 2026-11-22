# study15. 성능, 캐시, 비동기

## ① 목표

목록을 짧게 기억하고, 응답을 막지 않는 뒷일, 그리고 async 라우트가 이벤트 루프를 멈추는 경우를 구분한다.

## ② 📖 이론

### 왜 쓰는지

같은 목록을 매 요청마다 세면 DB가 같은 일을 반복한다. 반대로 캐시를 너무 오래 두면 방금 쓴 글이 안 보인다. 메일처럼 느린 일은 사용자가 응답을 받은 뒤에 해도 된다. async 함수 안에서 `time.sleep`을 하면 그 동안 다른 요청도 멈춘다.

### 핵심 개념

- `CACHE_TTL_MS=0`이면 캐시가 꺼진다. 테스트와 개발 기본값이다. 5000이면 5초.
- 글을 만들거나 고치거나 지우면 캐시를 비운다.
- `BackgroundTasks`는 응답을 보낸 뒤에 함수를 실행한다.
- `async def` 안의 `time.sleep`은 나쁜 예다. `await asyncio.sleep`은 기다리는 동안 다른 요청을 처리한다.
- 그냥 `def` 라우트의 `time.sleep`은 스레드 풀에서 돌므로 이벤트 루프 자체는 멈추지 않는다. 스레드 수만큼만 동시에 기다릴 수 있다.

### 비유

캐시는 계산대 옆의 메모지다. 재고를 바꿀 때마다 메모지를 버린다. 백그라운드 작업은 영수증을 건넨 뒤 창고에 전화하는 일이다. async 안의 `time.sleep`은 전화하는 동안 가게 문을 잠그는 일이다.

## ③ 🛠️ 실기

캐시 `app/cache.py`:

```python
def cache_get(key: str):
    ttl_ms = get_settings().cache_ttl_ms
    if ttl_ms <= 0:
        return None
    found = _store.get(key)
    if found is None:
        return None
    saved_at, value = found
    if (time.monotonic() - saved_at) * 1000 > ttl_ms:
        _store.pop(key, None)
        return None
    return value
```

줄별 설명:

1. 키로 저장값을 찾는다. 목록 키는 검색어, 정렬, 페이지, limit를 잇는다.
2. 설정의 TTL을 읽는다.
3. 0 이하면 항상 실패로 처리해 DB를 보게 한다.
4. 바로 끝난다.
5. 딕셔너리에서 찾는다.
6. 없으면 캐시 실패.
7. 끝.
8. 저장 시각과 값.
9. 몬otonic 시계로 나이를 잰다. 벽시계가 뒤로 가도 흔들리지 않는다.
10. 너무 오래됐으면 지운다.
11. 없는 것과 같이 취급한다.
12. 아직 신선하면 그 값을 돌려준다.

`list_posts`는 조회 전에 `cache_get`, 만든 뒤에 `cache_set`을 한다. 생성·수정·삭제는 `cache_clear`를 호출한다.

글 생성은 응답 뒤에 두 일을 예약한다.

```python
background_tasks.add_task(_notify_new_post, created.title)
background_tasks.add_task(_publish_post_created, created.id)
```

`_notify_new_post`는 제목을 로그로 찍는 자리다. 느린 메일 호출을 여기로 옮기면 사용자는 INSERT가 끝난 시점의 201을 받는다. `_publish_post_created`는 study17 웹소켓이 있을 때만 글 id를 보낸다.

비동기 비교 경로는 `demo`에만 있다. 각각 2초를 기다린다. 평소 테스트는 이 경로를 호출하지 않는다.

- `GET /async-demo/bad-async`: `async def` + `time.sleep(2)`. 이벤트 루프가 멈춘다.
- `GET /async-demo/good-async`: `await asyncio.sleep(2)`. 기다리는 동안 루프가 다른 일을 한다.
- `GET /async-demo/sync-def`: 일반 함수 + `time.sleep(2)`. 스레드 풀에서 잔다.

측정은 같은 목록을 두 번 호출해 터미널의 `request handled in ...ms`를 비교하는 것으로 시작한다. 캐시 TTL이 0이면 두 횟수가 비슷하다. 5000으로 올리고 글을 쓰지 않은 채 두 번째를 호출하면 DB를 건너뛴 만큼 짧아질 수 있다. 글을 쓴 직후에는 캐시가 비워지므로 다시 길어진다. 정밀한 부하는 이 로그 대신 별도 도구로 재고, 학습 단계에서는 이 전후 비교로 충분하다.

## ④ 🔗 연동 포인트

캐시 키에 `q`와 `page`가 들어 있으므로 study14의 쿼리가 그대로 키의 일부다. TTL은 `.env`라서 study8의 설정 경로를 탄다. 백그라운드 알림은 study13 메일 outbox를 나중에 호출할 자리이고, 웹소켓 전송은 study17의 `hub.broadcast`다. 테스트는 TTL 0과 `reset_idempotency` 안의 `cache_clear` 때문에 이전 테스트의 목록을 기억하지 않는다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 글을 썼는데 목록에 없음 | TTL 안에 옛 목록을 반환 | 쓰기 경로에서 `cache_clear`가 호출되는지 확인 |
| 테스트가 이전 목록을 봄 | 캐시와 idempotency를 안 비움 | autouse에서 `reset_idempotency` |
| 다른 요청이 같이 느려짐 | async 라우트에서 `time.sleep` | `await asyncio.sleep` 또는 일반 `def` |
| 응답이 메일 시간만큼 느림 | 메일 호출을 응답 전에 함 | `BackgroundTasks`로 옮긴다 |

## ⑥ 직접 해보기

1. `CACHE_TTL_MS=0`인 상태에서 목록을 두 번 호출하고 로그의 밀리초를 적는다.
2. 글 작성 응답이 돌아온 뒤에 터미널에 `[background] notified`가 찍히는지 본다.
3. `bad-async`와 `good-async`의 코드 차이만 읽고, 실제로 2초를 기다리는 호출은 필요할 때만 한다.

## ⑦ ☐ 체크리스트

- [ ] TTL 0이면 캐시가 동작하지 않는다는 것을 코드에서 찾을 수 있다.
- [ ] 쓰기 뒤에 목록 캐시가 비워진다.
- [ ] 알림은 응답 뒤에 실행된다.
- [ ] async 안의 블로킹 sleep과 `await`의 차이를 설명할 수 있다.
- [ ] 비동기 라우트

## ⑧ 다음 단계

요청 하나를 가볍게 만드는 방법을 봤으면, study16에서 그 프로세스를 컨테이너와 자동 테스트로 올리는 순서를 체크리스트로 정리한다.
