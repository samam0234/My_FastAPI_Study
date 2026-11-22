# study6. DB와 API 연동

## ① 목표

SQLite에 회원·게시글·댓글을 저장하고, 목록·상세·등록·수정·삭제를 공통 응답 형식으로 제공한다.

## ② 📖 이론

### 왜 쓰는지

메모리 리스트는 서버를 재시작하면 사라진다. 관계형 DB는 행으로 남고, 조건 검색과 페이지를 SQL에 맡길 수 있다. SQLAlchemy는 파이썬 클래스를 테이블로 쓰고, URL만 바꾸면 MySQL이나 MariaDB로 같은 클래스를 가져간다.

### 핵심 개념

- `DATABASE_URL`이 접속 정보다. 코드에 비밀번호를 적지 않는다.
- 기본값 `sqlite:///./demo.db`.
- MySQL과 MariaDB는 같은 계열 드라이버를 쓴다. `mysql+pymysql://user:password@localhost:3306/demo`
- 모델은 테이블, 저장소는 쿼리, 서비스는 "없으면 404, 남이면 403".
- 목록은 전체를 파이썬으로 자리지 않는다. `offset`/`limit`을 SQL에 넘긴다.
- 목록 JSON은 `items/skip`이 아니라 `data`와 `meta`다.

### 비유

SQLite 파일은 서랍 하나다. MySQL은 같은 양식의 서류함을 서버에 둔 것이다. 서류함 열쇠(`DATABASE_URL`)만 바꾸면 창고 직원이 가는 곳만 달라지고, 양식(모델)은 그대로다.

## ③ 🛠️ 실기

엔진은 URL을 보고 옵션을 고른다. `app/database.py`:

```python
def build_engine(url: str):
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)
```

줄별 설명:

1. URL을 받아 엔진을 만드는 함수. 테스트가 다른 URL을 넣을 때도 같은 규칙을 쓴다.
2. 추가 접속 옵션. 기본은 비어 있다.
3. SQLite일 때만 스레드 검사를 끈다. uvicorn은 요청 스레드가 바뀔 수 있다.
4. 그 옵션을 넣는다.
5. `pool_pre_ping`은 빌려 쓴 접속이 끊겼는지 다음 사용 전에 확인한다. MySQL에서 유용하고 SQLite에서도 해롭지 않다.

테이블은 `models/user.py`, `models/post.py`, `models/comment.py`다. 회원은 `email`이 유일하고, 글은 `title`, `body`, `tags`(JSON 문자열), `author_id`, `created_at`, `updated_at`을 가진다. 댓글은 `post_id`를 가리킨다.

저장소의 목록 쿼리는 필터 뒤 `count()`를 먼저 구하고, 그 다음 `offset((page - 1) * limit).limit(limit)`를 적용한다. 정렬은 `createdAt`, `-createdAt`, `-commentCount`만 허용한다. 댓글 수 정렬은 댓글 테이블을 그대로 붙이지 않고, 글 id별 개수 서브쿼리를 붙인다. 그대로 붙이면 댓글 수만큼 글 행이 늘어난다.

서비스가 만드는 목록 응답:

```json
{
  "data": [
    {
      "id": 1,
      "title": "첫 글",
      "body": "안녕하세요",
      "tags": ["intro"],
      "author": { "id": 3, "nickname": "mina" },
      "commentCount": 0,
      "createdAt": "2026-11-23T00:00:00Z",
      "updatedAt": "2026-11-23T00:00:00Z"
    }
  ],
  "meta": { "page": 1, "limit": 10, "total": 1, "totalPages": 1, "q": "" }
}
```

단건은 `{ "data": { ... } }`다. 생성은 201, 수정은 PATCH 200, 삭제는 204다.

SQLModel로 같은 일을 더 짧게 쓰는 예는 앱이 import하지 않는 `project/examples/sqlmodel_post.py`에 있다. 테이블 클래스 하나가 모델과 스키마를 겸한다. 이 게시판은 요청 스키마와 테이블을 일부러 나누기 위해 SQLAlchemy를 본 경로로 둔다. SQLModel을 실행해 보려면 그 파일의 주석대로 `pip install sqlmodel`을 한 뒤 예제만 실행한다.

MySQL로 바꿀 때 애플리케이션 코드는 수정하지 않는다.

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/demo
```

드라이버가 없으면 `pip install pymysql`을 한 뒤 서버를 다시 켠다. 테이블은 시작 시 `create_all`이 만든다. 이미 다른 모양으로 만들어진 SQLite 파일은 자동으로 마이그레이션되지 않으므로 파일을 지우거나 새 데이터베이스 이름을 쓴다.

댓글 API:

- `GET /api/posts/{id}/comments`
- `POST /api/posts/{id}/comments`
- `DELETE /api/comments/{id}`

글이 없으면 댓글 목록도 404다.

## ④ 🔗 연동 포인트

`DATABASE_URL`은 study0에서 만든 `.env`다. 응답의 `data`/`meta`는 study12 화면이 `data.data`와 `data.meta.total`로 읽는다. 작성자 id는 study7 토큰의 사용자와 비교해 403을 낸다. PostgreSQL로 URL만 바꾸는 절차는 study11에 적혀 있고, 이 단계의 기본 실습은 SQLite로 끝낸다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `no such column` | 옛 SQLite 파일 | db 파일을 삭제하고 재시작 |
| MySQL 연결 거부 | 서버가 꺼져 있거나 URL의 호스트·포트가 다름 | DB가 떠 있는지, 계정과 DB 이름이 있는지 확인 |
| `Access denied` | 비밀번호가 URL과 다름 | `.env`만 수정. 코드에 비밀번호를 붙이지 않는다 |
| 목록이 느리고 메모리를 많이 씀 | 전체를 읽고 파이썬에서 자르는 코드로 되돌림 | `offset`/`limit` 쿼리를 유지 |
| 댓글 수 정렬에서 글이 중복 | 댓글 행과 직접 join | 개수 서브쿼리를 join |

## ⑥ 직접 해보기

1. 가입 → 글 작성 → 목록 → 상세 → PATCH → DELETE 순서로 호출해 상태 코드를 적는다.
2. 글 3개를 만들고 `page=2&limit=2`의 `meta.totalPages`를 계산과 비교한다.
3. `.env`의 MySQL 주석을 읽고, 지금 프로세스가 실제로 어느 URL을 쓰는지 `DATABASE_URL`로 확인한다. 서버가 없다면 SQLite를 유지한다.

## ⑦ ☐ 체크리스트

- [ ] 모델, 저장소, 서비스, 라우터 순서로 CRUD가 나뉘어 있다.
- [ ] 목록 SQL이 `offset`/`limit`을 쓴다.
- [ ] 단건은 `data`, 목록은 `data`와 `meta`다.
- [ ] 접속 문자열은 `.env`에만 있다.
- [ ] SQLAlchemy / SQLModel + MySQL
- [ ] 목록 응답을 `items/total/skip/limit`에서 `data`+`meta`(`page`, `limit`, `total`, `totalPages`)로

## ⑧ 다음 단계

행이 저장되면 study7에서 그 행의 주인만 글을 고칠 수 있도록 로그인 토큰을 붙인다.
