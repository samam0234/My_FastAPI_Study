# study17. 실시간과 확장

## ① 목표

웹소켓으로 새 글의 id만 알리고, 알림과 파일 처리가 게시판 본문 API와 어떻게 나뉘는지 연결한다.

## ② 📖 이론

### 왜 쓰는지

목록 API는 클라이언트가 다시 물어봐야 새 글을 안다. 웹소켓은 서버가 먼저 한 줄을 보낼 수 있다. 그 한 줄에 글 전체를 넣으면 권한과 캐시와 문서 크기가 한곳에 섞인다. id만 보내고, 본문은 기존 `GET /api/posts/{id}`로 다시 읽는다.

### 핵심 개념

- 경로는 `/ws/posts`다. `/api` 접두어 밖에 둔다.
- 서버는 받는 텍스트에 답하지 않고, 연결을 유지하다가 새 글 id를 JSON으로 보낸다.
- 메시지 모양은 `{"event": "post.created", "id": 1}`뿐이다.
- 연결이 끊기면 목록에서 뺀다. 보내기에 실패한 소켓도 뺀다.
- 파일 업로드는 study13의 HTTP API로 남긴다. 웹소켓으로 파일을 흘리지 않는다.

### 비유

웹소켓은 매장 안의 벨이다. 벨은 "몇 번 주문이 들어왔다"만 알린다. 주문 내용은 다시 창구에서 확인한다.

## ③ 🛠️ 실기

`project/app/realtime.py` 전체 구조:

```python
class Hub:
    def __init__(self) -> None:
        self._sockets: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sockets.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._sockets:
            self._sockets.remove(websocket)

    async def broadcast(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for socket in self._sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.disconnect(socket)

hub = Hub()

@router.websocket("/ws/posts")
async def posts_socket(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)
```

줄별 설명:

1. 연결을 모아 두는 객체.
2. 생성자.
3. 소켓 리스트. 프로세스가 하나일 때만 이 리스트가 맞다. 프로세스가 여러 개면 이 메모리는 서로 보이지 않는다.
4. 빈 줄.
5. 연결을 받아들이는 비동기 함수.
6. 핸드셰이크를 끝낸다. 이 줄 전에 메시지를 보내면 실패한다.
7. 목록에 넣는다.
8. 빈 줄.
9. 목록에서 제거한다. 동기 함수로 충분한 이유는 리스트 조작만 하기 때문이다.
10. 이미 빠진 소켓을 다시 빼지 않는다.
11. 제거.
12. 빈 줄.
13. 모든 연결에 같은 JSON을 보낸다.
14. 실패한 소켓을 모아 둔다. 반복 중에 리스트를 바로 고치면 순서가 꼬인다.
15. 현재 연결을 하나씩.
16. 보내기를 시도한다.
17. JSON 텍스트로 전송한다.
18. 끊긴 연결은 예외가 된다.
19. 나중에 제거하려고 표시한다.
20. 실패분을 제거한다.
21. 목록에서 뺀다.
22. 클래스 끝.
23. 빈 줄.
24. 프로세스 안의 허브는 하나다.
25. 빈 줄.
26. `/ws/posts` 웹소켓 경로.
27. 함수는 async여야 `await`를 쓸 수 있다.
28. 목록에 등록하고 accept한다.
29. 끊김을 예외로 받는다.
30. 클라이언트가 보내는 텍스트는 읽기만 하고 방송하지 않는다. 빈 루프를 두지 않으면 연결이 바로 끝난다.
31. 한 줄을 받을 때까지 기다린다.
32. 브라우저가 닫히면 이 예외가 난다.
33. 목록에서 제거한다.

글 생성 서비스는 응답 뒤에 `_publish_post_created`를 실행한다. `demo`에는 `realtime` 모듈이 없어서 그 함수는 바로 반환한다. `project`에서는 `hub.broadcast({"event": "post.created", "id": post_id})`를 호출한다.

알림을 화면에서 쓰려면 웹소켓 메시지를 받은 뒤 그 id로 `GET /api/posts/{id}`를 호출해 카드를 추가하면 된다. 본문을 소켓에서 조립하지 않는다.

## ④ 🔗 연동 포인트

study15의 백그라운드 작업이 이 방송을 호출한다. 그래서 201 응답이 소켓 전송을 기다리지 않는다. 받은 id의 상세 조회는 study4 경로다. 파일은 study13 `POST /api/uploads`로 따로 올리고, 필요하면 글 본문에 저장된 파일 이름만 적는다. 프로세스를 두 개 띄우면 서로 다른 메모리 허브라 소켓이 반만 받는다. 그때는 이 리스트 대신 공유 저장소가 필요하지만, 이 학습 앱은 프로세스 하나로 동작을 확인한다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 연결 즉시 종료 | accept 전에 send하거나 수신 루프가 없음 | `accept` 후 `receive_text` 루프를 유지 |
| 글을 써도 소켓이 조용함 | demo 앱을 보고 있음 | project 앱의 `/ws/posts`에 접속 |
| 메시지에 본문이 없음 | 일부러 id만 보냄 | 이어서 GET 상세를 호출 |
| 서버를 둘 띄우면 알림이 반만 옴 | 허브가 프로세스 메모리 | 학습 중에는 프로세스를 하나로 둔다 |

## ⑥ 직접 해보기

1. project 테스트 `test_websocket_accepts`가 연결을 여는지 확인한다.
2. `/ws/posts`에 접속한 뒤 글을 작성하고, 방송 함수가 id만 넣는지 코드를 따라간다.
3. 업로드 API와 웹소켓 경로가 다른 파일인 것을 말한다.

## ⑦ ☐ 체크리스트

- [ ] 웹소켓 경로는 `/ws/posts`다.
- [ ] 방송 JSON은 `event`와 `id`만 가진다.
- [ ] 끊긴 소켓은 목록에서 제거된다.
- [ ] demo는 이 모듈이 없어도 글 작성이 된다.
- [ ] 파일은 HTTP 업로드로 따로 처리한다.

## ⑧ 다음 단계

실시간 알림 다음에, study18에서 문서 내용만을 근거로 답하는 AI 호출과 스트리밍, MCP 도구를 같은 FastAPI에 붙인다.
