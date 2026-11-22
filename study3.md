# study3. 데이터 다루기

## ① 목표

요청과 응답의 모양을 Pydantic으로 고정하고, 파이썬 필드와 JSON 필드 이름을 역할에 맞게 나눈다.

## ② 📖 이론

### 왜 쓰는지

딕셔너리는 오타를 실행해 봐야 안다. 스키마는 요청이 함수에 들어가기 전에 빠지거나 틀린 값을 거절하고, `/docs`에 그 모양을 보여 준다. DB 모델과 응답 모델을 나누면 비밀번호 해시 같은 컬럼이 JSON에 실려 나가지 않는다.

### 핵심 개념

- **BaseModel**: 필드 타입을 선언하는 클래스.
- **요청 스키마 / 응답 스키마**: 들어오는 값과 나가는 값을 다른 클래스로 둔다.
- **alias_generator**: 파이썬은 `created_at`, JSON은 `createdAt`처럼 이름을 바꿔 준다.
- **from_attributes**: ORM 객체의 속성에서도 값을 읽게 한다.
- **로컬 저장**: 이 단계의 영속 저장은 아직 규칙이 아니라 파일이다. SQLite 파일 `demo.db`가 그 역할을 하고, 컬럼 설계는 study6에서 한다.

### 비유

스키마는 주문서 양식이다. 칸에 없는 항목은 주방에 전달되지 않고, 손님에게 돌려주는 영수증에는 원가(해시)를 인쇄하지 않는다. camelCase 별칭은 같은 내용을 다른 언어 습관으로 적는 번역 도장이다.

## ③ 🛠️ 실기

`project/app/schemas/common.py` 전체가 별칭 규칙이다.

```python
from pydantic import BaseModel, ConfigDict


def to_camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(part.capitalize() for part in tail if part)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
```

줄별 설명:

1. Pydantic의 모델 부모와 설정 타입.
2. 빈 줄.
3. `created_at` 같은 이름을 받아 camelCase로 바꾸는 함수.
4. 첫 조각은 그대로 두고, 나머지는 앞글자만 대문자로 붙인다.
5. `created` + `At`. 빈 조각은 무시한다.
6. 빈 줄.
7. 이후 스키마는 이 클래스를 상속한다.
8. 설정을 한곳에 모은다.
9. 필드 이름마다 `to_camel`을 호출해 JSON 이름을 만든다.
10. 파이썬 이름(`created_at`)으로도 값을 넣을 수 있다. 테스트와 내부 코드가 편하다.
11. ORM 객체의 속성을 읽어 스키마를 만들 수 있다.
12. 설정 끝.
13. 클래스 끝.

게시글 응답은 이 규칙을 상속한다. 비밀번호에 해당하는 필드는 아예 없다.

```python
class PostResponse(APIModel):
    id: int
    title: str
    body: str
    tags: list[str]
    author: Author | None = None
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime
```

JSON으로 나가면 키는 `commentCount`, `createdAt`, `updatedAt`이 된다. FastAPI의 `response_model`은 기본적으로 별칭으로 직렬화한다.

회원 응답 `UserResponse`에는 `id`, `email`, `nickname`만 있다. `hashed_password`를 스키마에 넣지 않는 것이 필터다.

요청 쪽 `PostCreate`는 `title`, `body`, `tags`다. 한 단어라 별칭이 달라도 철자가 같다. 별칭의 효과는 응답의 시각과 개수 필드에서 드러난다.

화면과 묶는 바인딩은 백엔드에 양방향 바인딩이 없다. 프론트는 응답 JSON의 `data`를 state에 넣고, 입력칸의 state를 다시 JSON 바디로 POST한다. `demo/frontend/src/App.jsx`의 `createPost({ title, body, tags })`가 그 연결이다.

로컬 파일 저장은 `.env`의 `DATABASE_URL=sqlite:///./demo.db`다. 서버를 끄면 테이블 내용은 파일에 남는다. 스키마를 바꾼 뒤에는 옛 파일을 지워야 새 컬럼이 만들어진다. `create_all`은 없는 테이블만 만들고, 있는 테이블의 컬럼을 고치지 않는다.

## ④ 🔗 연동 포인트

이 스키마가 study5의 검증 메시지, study6의 저장 컬럼, study12 화면의 `post.body` / `post.createdAt`과 맞물린다. 프론트는 snake_case 키를 읽지 않는다. 백엔드를 다른 구현으로 바꿔도 이 camelCase 봉투를 지키면 화면 코드를 그대로 둔다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 응답에 `created_at`만 보임 | 모델을 `APIModel`이 아닌 `BaseModel`로 둠 | `APIModel`을 상속 |
| 요청에 `createdAt`을 넣었더니 무시 | 생성 스키마에 그 필드가 없음 | 서버가 시각을 채운다. 클라이언트가 보내지 않는다 |
| ORM을 반환했는데 500 | `from_attributes` 없이 응답 모델을 강제 | `APIModel` 설정을 확인 |
| 옛 SQLite에서 컬럼이 없다고 함 | 이전 스키마의 파일이 남음 | `demo.db`를 지우고 서버를 다시 시작 |

## ⑥ 직접 해보기

1. 글을 하나 만들고 응답에 `createdAt`이 있고 `created_at`이 없는지 본다.
2. 회원가입 응답 본문에 `password` 문자열이 없는지 확인한다.
3. `demo.db`를 지운 뒤 서버를 다시 켜서 빈 목록이 나오는지 본다.

## ⑦ ☐ 체크리스트

- [ ] 요청 스키마와 응답 스키마를 다른 클래스로 두었다.
- [ ] 응답에 비밀번호 해시가 없다.
- [ ] `created_at`이 JSON에서 `createdAt`으로 나간다.
- [ ] SQLite 파일이 재시작 후에도 데이터를 남기는 것을 확인했다.
- [ ] 응답 모델에서 필드 이름을 camelCase로 (`alias_generator`)

## ⑧ 다음 단계

모양을 정했으니 study4에서 그 모양이 어느 URL로 들어오고, 실패하면 어떤 JSON으로 나가는지 경로와 오류 형식을 고정한다.
