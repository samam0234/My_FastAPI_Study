# study16. 운영과 CI

## ① 목표

Docker로 같은 명령을 재현하고, GitHub Actions에서 테스트를 돌리며, 로그와 백업을 빠뜨리지 않는 체크리스트를 만든다.

## ② 📖 이론

### 왜 쓰는지

내 컴퓨터에서만 되는 실행은 패키지 버전이 달라지면 깨진다. 이미지는 그 버전을 고정하고, Actions는 푸시할 때마다 `pytest`를 다시 실행한다. 백업이 없으면 SQLite 파일 하나가 곧 전체 데이터다.

### 핵심 개념

- `Dockerfile`은 파이썬 이미지 위에 `requirements.txt`를 설치하고 uvicorn을 실행한다.
- `docker-compose.yml`의 기본 서비스는 API와 SQLite다. PostgreSQL은 `postgres` 프로필로만 켠다.
- 컨테이너 안에서 바인드 주소는 `0.0.0.0`이다. `127.0.0.1`이면 컨테이너 바깥에서 접속하지 못한다.
- GitHub Actions 워크플로는 `demo`와 `project`를 각각 설치하고 `pytest -q`를 실행한다.
- 로그는 uvicorn 터미널과 `logger.exception`이다. 이 학습 범위에는 외부 모니터링 서비스를 붙이지 않는다.
- 백업 스크립트는 SQLite 파일을 `backups/`로 복사한다. 서버형 DB의 백업은 그 DB의 dump 도구를 쓴다.

### 비유

Dockerfile은 이사 상자 목록이다. Actions는 상자를 열 때마다 물건이 빠지지 않았는지 세는 검수다. 백업은 상자 하나의 복사본을 다른 방에 두는 일이다.

## ③ 🛠️ 실기

`project/Dockerfile`의 명령:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV DATABASE_URL=sqlite:///./demo.db
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

줄별 설명:

1. 공식 파이썬 3.12의 얇은 이미지.
2. 이후 명령의 작업 폴더.
3. 의존성 목록만 먼저 복사한다. 소스만 바뀔 때 설치 층을 다시 쓰지 않기 위해서다.
4. 이미지 안에 패키지를 설치한다.
5. 애플리케이션 소스.
6. 이미지 기본 DB. compose나 실행 옵션으로 덮어쓸 수 있다.
7. 문서용 포트. 실제로 여는 것은 아래 CMD와 compose의 ports다.
8. 리로드 없이 모든 인터페이스의 8000번을 연다.

compose를 앱만 올리려면 `project`에서 `docker compose up --build`다. PostgreSQL까지 보려면 `docker compose --profile postgres up`이고, 그때 `DATABASE_URL`을 `postgresql+psycopg://demo:demo@postgres:5432/demo`로 바꿔야 한다. 이 저장소를 만든 환경에서는 그 실서버 접속을 완료로 보지 않는다.

워크플로 `.github/workflows/test.yml`은 `push`와 `pull_request`에 `demo`, `project` 두 폴더를 행렬로 돌린다. 각 폴더에서 pip로 `requirements.txt`를 설치하고 `pytest -q`를 실행한다.

SQLite 백업:

```powershell
cd project
.venv\Scripts\Activate.ps1
python scripts/backup_sqlite.py
```

`DATABASE_URL`이 sqlite 파일이고 그 파일이 있으면 `backups/` 아래에 시각이 붙은 복사본이 생긴다. `backups/`는 Git에 올리지 않는다.

운영 체크리스트:

- [ ] 이미지 빌드가 `requirements.txt` 설치에서 멈춘다면 버전 핀을 확인한다.
- [ ] 컨테이너 로그에 `Uvicorn running`과 바인드 `0.0.0.0:8000`이 보인다.
- [ ] 호스트에서 `http://127.0.0.1:8000/health`가 ok다.
- [ ] `SECRET_KEY`를 이미지에 박아 두지 않고 실행 환경 변수로 넣었다.
- [ ] Actions의 demo와 project 테스트가 통과한다.
- [ ] SQLite를 쓰면 `backup_sqlite.py` 복사본이 생긴다.
- [ ] 로그에 비밀번호와 토큰 원문이 없다.
- [ ] 디스크가 차기 전에 `uploads/`와 `backups/`의 크기를 본다.

## ④ 🔗 연동 포인트

study10의 환경 변수가 컨테이너의 `environment`로 들어간다. study11의 PostgreSQL URL은 프로필을 켠 뒤에만 의미가 있다. study9의 pytest가 Actions의 명령과 같다. 업로드 파일은 컨테이너를 지우면 사라지므로 운영에서는 `uploads`를 볼륨으로 남겨야 한다. compose의 `board-data` 볼륨이 그 자리다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 호스트에서 연결 거부 | 프로세스가 127.0.0.1만 연다 | CMD의 `--host 0.0.0.0` |
| compose가 DB에 못 감 | URL이 localhost | 서비스 이름 `postgres`를 호스트로 |
| Actions만 실패 | 로컬 가상환경에만 있는 패키지 | `requirements.txt`에 그 패키지를 고정 |
| 백업 스크립트가 바로 종료 | URL이 sqlite 파일이 아님 | 메시지대로 서버형 DB는 dump 도구를 쓴다 |

## ⑥ 직접 해보기

1. Docker가 설치되어 있다면 `project`에서 이미지를 빌드하고 `/health`를 연다. 없으면 Dockerfile의 호스트가 `0.0.0.0`인지만 확인한다.
2. `backup_sqlite.py`를 실행하거나, db 파일이 없을 때의 메시지를 읽는다.
3. 워크플로 파일에서 `demo`와 `project`가 둘 다 `pytest -q`를 실행하는지 표시한다.

## ⑦ ☐ 체크리스트

- [ ] Dockerfile이 리로드 없이 `0.0.0.0`을 연다.
- [ ] compose 기본값은 SQLite이고 PostgreSQL은 프로필이다.
- [ ] GitHub Actions가 두 앱의 테스트를 실행한다.
- [ ] 백업 폴더는 Git에 올라가지 않는다.
- [ ] 운영 체크리스트의 로그·비밀·헬스 항목을 읽었다.

## ⑧ 다음 단계

프로세스가 안정적으로 뜨면 study17에서 새 글이 생겼다는 사실을 연결된 클라이언트에 바로 알린다.
