# study12. 프론트와 UI 연동

## ① 목표

FastAPI의 JSON을 React 화면의 상태, 입력 폼, 오류 문장과 연결한다.

## ② 📖 이론

### 왜 쓰는지

API는 데이터를 줄 뿐 화면을 그리지 않는다. 화면은 목록을 state에 넣고, 입력칸의 state를 JSON으로 다시 보낸다. UI 라이브러리나 폼 라이브러리를 나중에 얹어도 이 왕복의 모양은 바뀌지 않는다.

### 핵심 개념

- 이 저장소의 화면은 React와 Vite다. 컴포넌트 라이브러리는 쓰지 않고 `index.css`의 `.card`로 칸을 나눈다. 라이브러리를 도입해도 `api.listPosts()`의 반환값만 카드에 넘기면 된다.
- 상태 관리는 `useState`다. 로그인 정보만 `localStorage`에 남겨 새로고침을 견딘다. 전역 상태 라이브러리로 옮겨도 저장할 값은 `token`, `id`, `nickname` 세 가지다.
- 폼은 제어 컴포넌트다. 가입은 이메일·비밀번호·닉네임, 글은 제목·본문·태그 문자열이다. 폼 라이브러리를 쓰면 같은 필드를 스키마로 선언하고, 제출 함수는 여전히 `api.createPost`를 호출한다.
- 오류는 `error.message`와 `fields`를 한 문장으로 합쳐 상단 박스에 보여 준다.

### 비유

API는 주문서 원본이고 화면은 계산대다. 계산대의 기계(폼 라이브러리)를 바꿔도 주문서 칸 이름은 `title`, `body`, `accessToken` 그대로다.

## ③ 🛠️ 실기

`frontend/src/api.js`의 요청 함수가 계약의 중심이다.

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, { method = "GET", body, token } = {}) {
  const headers = {};
  let payload;
  if (body !== undefined) {
    headers["Content-Type"] = "application/json; charset=utf-8";
    payload = JSON.stringify(body);
  }
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE_URL}${path}`, { method, headers, body: payload });
  const data = res.headers.get("content-type")?.includes("application/json") ? await res.json() : null;
  if (!res.ok) {
    const error = data?.error;
    const fieldText = error?.fields
      ? " " + Object.entries(error.fields).map(([key, messages]) => `${key}: ${messages.join(", ")}`).join(" / ")
      : "";
    throw new Error((error?.message || `요청 실패 (${res.status})`) + fieldText);
  }
  return data;
}
```

줄별 설명:

1. `demo` 화면의 기본값은 8001, `project` 화면의 기본값은 8000이다. `.env`의 `VITE_API_BASE_URL`이 있으면 그 값이 이긴다.
2. 빈 줄.
3. 경로와 옵션을 받아 `fetch`를 한곳으로 모은다.
4. 헤더 객체.
5. 바디는 있을 때만 만든다. DELETE는 바디가 없어야 한다.
6. JSON을 보낼 때 타입을 적는다.
7. 객체를 문자열로 바꾼다. 키는 이미 camelCase다.
8. 토큰이 있으면 Bearer 헤더를 붙인다. 로그인 전에는 이 줄이 실행되지 않는다.
9. 백엔드로 요청을 보낸다.
10. JSON이 아니면 `null`이다. 204 응답이 여기 해당한다.
11. 상태 코드가 실패면 예외로 바꾼다. 화면의 `catch`가 받는다.
12. 서버가 만든 `error` 객체.
13. `fields`가 있으면 `title: 1~200자로...`처럼 붙인다.
14. 여러 필드를 슬래시로 잇는다.
15. 필드가 없으면 빈 문자열.
16. 메시지와 필드를 합쳐 예외로 던진다.
17. 실패 처리 끝.
18. 성공 JSON을 그대로 반환한다. 목록이면 `data`와 `meta`가 들어 있다.

`App.jsx`는 `api.listPosts({ page, limit, q })`의 `data.data`를 글 배열로, `data.meta`를 페이지 표시로 쓴다. 글 작성은 `{ title, body, tags }`를 POST한다. 태그는 쉼표 문자열을 배열로 나눈 뒤 보낸다. 삭제 버튼은 `post.author.id === auth.id`일 때만 그린다. 서버가 403을 주는 것이 진짜 검사이고, 화면의 조건은 버튼을 숨기는 일뿐이다.

실행은 API를 켠 다음 다른 터미널에서 한다.

```powershell
cd project\frontend
npm install
copy .env.example .env
npm run dev
```

화면은 `http://localhost:3000`이다. 이 출처는 백엔드 `CORS_ORIGINS`에 들어 있어야 한다.

## ④ 🔗 연동 포인트

study5의 400 필드 메시지가 이 파일에서 문장이 된다. study6의 `meta.totalPages`가 이전/다음 버튼을 끄고 켠다. study7의 `accessToken`이 localStorage를 거쳐 다음 요청의 헤더가 된다. 화면은 FastAPI의 `/docs`와 같은 계약을 보므로, 백엔드 경로를 바꾸면 `api.js`의 문자열만 같이 바꾼다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| Failed to fetch | API가 꺼져 있거나 포트가 다름 | uvicorn 포트와 `VITE_API_BASE_URL`을 맞춘다 |
| CORS error | 출처가 허용 목록에 없음 | `http://localhost:3000`을 `CORS_ORIGINS`에 넣는다 |
| 로그인했는데 작성자 버튼이 안 보임 | 응답을 `access_token`으로 읽음 | `data.accessToken`과 `data.user`를 쓴다 |
| 목록이 undefined | `items`를 읽음 | `data.data`와 `data.meta`를 쓴다 |

## ⑥ 직접 해보기

1. 화면에서 가입하고 글을 쓴 뒤 Network 탭의 요청 경로가 `/api/posts`인지 본다.
2. 제목을 비우고 제출해 상단 박스에 필드 문장이 보이는지 확인한다.
3. 검색어를 넣고 다음 페이지 버튼이 `totalPages`에 맞게 꺼지는지 본다.

## ⑦ ☐ 체크리스트

- [ ] 화면 주소와 API 주소를 환경 변수로 분리했다.
- [ ] 로그인 토큰이 Authorization 헤더로 나간다.
- [ ] 목록은 `data`/`meta`, 오류는 `error.message`를 읽는다.
- [ ] 내 글에만 삭제 버튼이 있고, 권한의 최종 판단은 서버다.
- [ ] 컴포넌트 라이브러리 없이도 같은 JSON을 카드로 그릴 수 있다.

## ⑧ 다음 단계

화면이 API에 붙었으면 study13에서 파일, 메일, 결제 초안, 소셜 로그인 주소를 같은 백엔드에 추가한다.
