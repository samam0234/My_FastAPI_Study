# study18. AI 연동과 MCP

## ① 목표

문서 텍스트 안에서만 답하는 API, 그 답의 스트리밍, 그리고 같은 규칙을 도구로 노출하는 최소 MCP 서버를 FastAPI 학습 앱에 붙인다.

## ② 📖 이론

### 왜 쓰는지

모델은 그럴듯한 문장을 학습 데이터에서 만들 수 있다. 문서 질문에서는 그 습관이 위험하다. 올려 둔 텍스트에 없는 내용은 "찾을 수 없습니다"가 맞다. 키가 없을 때도 이 규칙이 동작해야 테스트가 외부 API에 의존하지 않는다.

### 핵심 개념

- `POST /api/ai/documents`: `documentId`와 `text`를 메모리 청크로 저장한다.
- `POST /api/ai/ask`: 질문과 겹치는 청크만 모아 답한다. 없으면 404.
- `GET /api/ai/ask/stream`: 같은 답을 `text/event-stream`으로 단어씩 보낸다.
- `resolve_provider()`: `LLM_PROVIDER`와 키가 없으면 `mock`. OpenAI 키가 있고 제공자가 openai일 때만 네트워크를 호출한다.
- MCP 예시는 HTTP 서버와 별개 프로세스다. 도구 이름은 `ask_document`이고, 인자로 문서 텍스트와 질문을 받는다.

### 비유

모델은 말을 잘하는 상담원이고, 청크 검색은 상담원 앞에 펼쳐 둔 서류다. 서류에 없는 질문은 "그 문서는 여기 없습니다"로 끝낸다. MCP는 그 상담원을 다른 프로그램이 버튼 하나로 부르게 하는 교환원이다.

## ③ 🛠️ 실기

검색과 답은 `project/app/ai_engine.py`에 있다.

```python
def answer_from_hits(hits: list[dict]) -> str:
    if not hits:
        return "찾을 수 없습니다"
    lines = [f"(발췌 {index}) {hit['text']}" for index, hit in enumerate(hits, start=1)]
    return "문서에서 찾은 내용입니다.\n" + "\n".join(lines)

def resolve_provider() -> str:
    settings = get_settings()
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider == "openai" and settings.openai_api_key:
        return "openai"
    if provider == "ollama":
        return "ollama"
    if not provider and settings.openai_api_key:
        return "openai"
    return "mock"
```

줄별 설명:

1. 겹친 청크가 없을 때의 문장과 있을 때의 문장을 나눈다.
2. 근거가 없으면 이 문장만 반환한다. 모델이 지어내지 않게 하는 분기이다.
3. 청크마다 `(발췌 1)`처럼 번호를 붙인다.
4. 번호를 1부터 센다.
5. 머리 문장과 발췌를 합친다.
6. 빈 줄.
7. 어느 구현을 쓸지 환경 변수로 고른다.
8. 설정에서 키를 읽는다. 키 자체는 로그에 찍지 않는다.
9. `LLM_PROVIDER`가 없으면 빈 문자열이다.
10. openai라고 적었고 키도 있을 때만 openai.
11. ollama라고 적으면 ollama 쪽으로 이름만 돌린다. 이 학습 코드의 실제 HTTP 호출은 openai 분기에만 있다.
12. 제공자를 비워 두고 키만 있으면 openai로 본다.
13. 그 외에는 mock이다. 테스트는 이 값을 강제한다.

질문 라우터는 문서가 없으면 404로 다음 문장을 준다. "해당 문서의 인덱스를 찾을 수 없습니다. 문서를 다시 업로드해 주세요." 모델 호출이 예외를 일으키면 503과 `AI 모델 호출 실패`다.

스트리밍은 한 줄에 `data: {"text": "..."}`를 보내고 마지막에 `data: {"done": true}`를 보낸다. 화면은 줄을 이어 붙이면 답이 점점 길어진다.

OpenAI를 쓰는 분기는 `response_format`으로 JSON만 받도록 요청한다. 키가 없으면 이 코드는 실행되지 않는다.

MCP 서버는 `project/examples/mcp/server.py`다. 표준 입력으로 JSON-RPC 한 줄을 받는다.

- `initialize`: 서버 이름 `board-ask`
- `tools/list`: `ask_document`
- `tools/call`: `text`와 `question`으로 위의 `answer_from_hits`를 호출

실행은 project 폴더에서 `python examples/mcp/server.py`다. HTTP 포트와는 별개라 FastAPI를 끄고 있어도 도구 규칙만 확인할 수 있다.

이 경로는 두 미니 프로젝트에서 FastAPI가 맡았던 일과 같은 방향이다.

- [DocuForge](https://app.notion.com/p/40bd7dec5e2e818d9c91c6fb26dccc4c)에서 FastAPI는 문서 추출 뒤의 요약과 `/ask`를 맡았다. 사용자와 DB는 앞단이 가지고, 인덱스가 없으면 404, 모델 실패는 503이었다. 이 학습 앱의 `/api/ai/ask`는 그 상태 코드와 "발췌 번호" 규칙을 작게 다시 만든 것이다. 추출기(PDF, DOCX, PPTX)와 앞단 서버는 이 저장소에 넣지 않는다.
- [SocialForge](https://app.notion.com/p/40bd7dec5e2e81cb8c76d6d66962619a)에서 FastAPI는 OpenAI, Anthropic, mock 중 하나를 고르는 AI 서버였다. `resolve_provider()`가 그 선택 순서(환경 변수, 그 다음 키, 없으면 mock)를 따른다. 이 저장소의 생성 대상은 소셜 문구가 아니라 문서 발췌 답변이다.

## ④ 🔗 연동 포인트

study13 업로드로 받은 텍스트를 `POST /api/ai/documents`의 `text`로 넣으면 파일과 질문이 연결된다. 이 예제는 그 연결을 자동으로 하지 않고, 두 API를 순서대로 부르게 남겨 두었다. 스트리밍 URL은 화면의 EventSource 또는 fetch 스트림이 읽는다. MCP는 에디터나 다른 프로세스가 같은 `ask_document` 규칙을 부를 때 쓴다. 키는 `.env`의 `OPENAI_API_KEY`이고 응답 본문에는 넣지 않는다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 항상 "찾을 수 없습니다" | 질문 토큰이 청크와 안 겹침 | 문서에 있는 단어를 질문에 넣는다 |
| 404 | documentId가 메모리에 없음 | 서버를 재시작하면 인덱스가 사라진다. 다시 등록한다 |
| 503 | 키는 있는데 호출이 실패 | 키를 비우면 mock으로 돌아간다. 실패 원인은 로그의 예외 메시지 |
| 스트림이 한 번에 보임 | 클라이언트가 끝날 때까지 모아서 그림 | 줄 단위로 화면에 추가한다 |

## ⑥ 직접 해보기

1. 문서에 "FastAPI는 타입 힌트로 요청을 검증한다."를 넣고 "타입 힌트"로 질문한다. 답에 `(발췌 1)`이 있는지 본다.
2. 없는 documentId로 질문해 404 문장을 확인한다.
3. MCP 예제 파일의 `tools/list`가 `ask_document`만 내보내는지 코드를 읽고, 한 줄 JSON으로 `tools/call`을 넣어 본다.

## ⑦ ☐ 체크리스트

- [ ] 키가 없으면 네트워크를 호출하지 않는다.
- [ ] 근거 청크가 없으면 "찾을 수 없습니다"다.
- [ ] 없는 문서는 404, 모델 호출 실패는 503이다.
- [ ] 스트리밍은 `text/event-stream`이다.
- [ ] MCP 도구 `ask_document`가 같은 발췌 규칙을 쓴다.
- [ ] DocuForge의 `/ask`와 SocialForge의 제공자 선택을 FastAPI 역할로만 연결했다.

## ⑧ 다음 단계

기초 게시판과 이 심화 기능을 한 서비스로 점검하는 순서는 studyFinal에 모아 두었다.
