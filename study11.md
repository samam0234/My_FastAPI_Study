# study11. DB 확장

## ① 목표

같은 SQLAlchemy 모델을 SQLite, MariaDB, PostgreSQL에 연결하는 차이와, MongoDB가 그 엔진에 들어가지 않는 이유를 구분한다.

## ② 📖 이론

### 왜 쓰는지

개발은 파일 하나인 SQLite로 충분하다. 여러 프로세스가 동시에 쓰면 서버형 DB가 필요하다. 모델을 다시 짜지 않고 접속 문자열과 드라이버만 바꾸는 것이 ORM을 쓰는 이유다.

### 핵심 개념

- **SQLite**: `sqlite:///./demo.db`. 서버 프로세스가 없다. `check_same_thread`가 필요하다.
- **MariaDB / MySQL**: `mysql+pymysql://user:password@localhost:3306/demo`. 드라이버 패키지는 `pymysql`.
- **PostgreSQL**: `postgresql+psycopg://user:password@localhost:5432/demo`. 드라이버는 `psycopg`(3).
- **MongoDB**: 문서 데이터베이스라 `create_engine`에 넣지 않는다. 예시는 `project/examples/mongodb_client.py`이고, 이 게시판의 본 경로는 아니다.
- **SQLModel**: SQLAlchemy 위에 스키마와 테이블을 한 클래스로 합친 도구. 예시는 `project/examples/sqlmodel_post.py`. 본 앱은 요청 스키마와 테이블을 나누려고 SQLAlchemy만 사용한다.

`pool_pre_ping=True`는 서버형 DB가 끊어 둔 접속을 다음 요청 전에 확인한다.

### 비유

SQLite는 책상 서랍, MariaDB와 PostgreSQL은 같은 서류 양식을 받는 두 창고다. 열쇠 문자열만 다르다. MongoDB는 서류철이 아니라 봉투 더미라, 서랍 열쇠로는 열리지 않는다.

## ③ 🛠️ 실기

애플리케이션이 URL을 해석하는 함수는 study6의 `build_engine` 그대로다. 바꾸면 안 되는 것은 라우터와 서비스다.

PostgreSQL을 연습용으로 띄우는 작성은 `project/docker-compose.yml`의 `postgres` 서비스다. 기본 `docker compose up`에는 포함되지 않고, 프로필을 지정할 때만 뜬다.

```powershell
cd project
docker compose --profile postgres up -d postgres
```

뜬 뒤에 앱의 환경 변수만 바꾼다.

```env
DATABASE_URL=postgresql+psycopg://demo:demo@localhost:5432/demo
```

패키지가 없으면 앱 폴더에서 `pip install "psycopg[binary]"`. 그 다음 uvicorn을 재시작한다. `create_all`이 빈 데이터베이스에 테이블을 만든다. 이미 데이터가 있는 SQLite와는 별개의 데이터베이스다.

MariaDB도 같은 자리다. 서버를 준비한 뒤 URL만 `mysql+pymysql://...`로 바꾼다. 포트 기본값은 3306이다.

MongoDB 예시는 실행 경로가 아니다. `examples/mongodb_client.py`는 `AsyncIOMotorClient`로 `posts` 컬렉션에 문서를 넣는 함수만 보여 준다. 컬럼 선언이 없고, 조인 대신 문서를 통째로 넣는다. 이 게시판의 `author_id` 외래 키 검사는 그 모델에 없다.

SQLModel 예시를 실행하려면 별도 설치가 필요하다.

```powershell
pip install sqlmodel
python examples/sqlmodel_post.py
```

출력은 `SQLModel 메모`다. 이 실행은 `demo.db`를 만들지 않고 메모리 엔진만 쓴다.

이 작업에서는 떠 있는 PostgreSQL에 접속해 테이블을 만드는 단계까지 확인하지 않았다. 컴포즈 파일과 URL, 드라이버 이름만 준비했다. 그래서 아래 PostgreSQL 항목은 비워 둔다.

## ④ 🔗 연동 포인트

study6의 저장소 코드는 엔진만 바꾸면 같은 CRUD를 수행한다. study16의 컨테이너는 기본으로 SQLite 파일을 볼륨에 둔다. PostgreSQL 프로필을 쓸 때는 `DATABASE_URL`을 compose 네트워크의 호스트 이름 `postgres`로 바꾼다. `localhost`는 컨테이너 안의 자기 자신을 가리키므로, 앱 컨테이너에서는 `postgres`라는 서비스 이름을 쓴다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `No module named 'psycopg'` | 드라이버 미설치 | `pip install "psycopg[binary]"` |
| `Can't connect` MySQL | 서버 중지 또는 포트 | 3306이 열려 있는지 확인 |
| PostgreSQL 비밀번호 실패 | compose의 `demo/demo`와 URL이 다름 | URL의 사용자와 비밀번호를 compose와 맞춘다 |
| 컨테이너에서 localhost 접속 실패 | localhost가 앱 컨테이너 자신 | 호스트 이름을 `postgres`로 |
| Mongo 예시를 SQLAlchemy URL에 넣음 | 엔진이 그 스킴을 모름 | Mongo는 별도 드라이버 예제로만 둔다 |

## ⑥ 직접 해보기

1. 지금 `.env`의 `DATABASE_URL`이 sqlite인지 확인하고, 앱이 그 파일로 목록을 읽는지 본다.
2. `examples/sqlmodel_post.py`를 설치 후 실행하거나, 설치하지 않는다면 클래스가 테이블과 모델을 겸한다는 점만 주석으로 확인한다.
3. compose의 postgres 프로필을 읽고, 앱 컨테이너에서 호스트 이름이 왜 `localhost`가 아닌지 한 문장으로 적는다.

## ⑦ ☐ 체크리스트

- [ ] SQLite, MariaDB, PostgreSQL의 URL 스킴을 구분한다.
- [ ] `build_engine`이 SQLite에만 `check_same_thread`를 넣는다.
- [ ] MongoDB 예시가 본 앱의 엔진을 쓰지 않는다.
- [ ] SQLModel 예시가 앱 시작 경로에 포함되지 않는다.
- [ ] PostgreSQL 연결 (`postgresql+psycopg://...`, PostgreSQL 페이지)

## ⑧ 다음 단계

DB를 유지한 채로, study12에서 이 JSON을 React 화면의 state와 입력 폼에 연결한다.
