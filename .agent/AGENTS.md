# 에이전트 공통 가이드라인 (인수인계 문서)

이 문서는 이 저장소에서 작업하는 모든 AI 에이전트(Claude, Grok, Codex 등)가 **공통으로** 지켜야 할 규칙을 정리한 인수인계 문서입니다.
`.claude/`, `.grok/`, `.codex/` 폴더의 에이전트별 문서는 이 문서를 기본으로 삼고, 도구별 특이사항만 추가로 기술합니다.

## 1. 저장소 개요

- Python [FastAPI](https://fastapi.tiangolo.com/) 학습 기록 저장소입니다. FastAPI는 타입힌트 기반 자동 문서화(Swagger/ReDoc), Pydantic 데이터 검증, ASGI 비동기 처리가 강점인 API 전용 프레임워크입니다.
- 공통 스펙: **`/posts` CRUD + `/auth/login`**을 처음부터 끝까지 사용합니다. 인메모리 → SQLAlchemy(DB) → JWT 인증 순으로 점진적으로 발전시킵니다.
- 학습 목표와 전체 로드맵은 [Notion: FastAPI 학습 목표](https://app.notion.com/p/FastAPI-3d6d7dec5e2e810fb6f5fa9e53bcb9a2) 페이지를 기준으로 삼습니다.
- `study0.md`, `study1.md`, `study2.md`, ... 순서로 학습 진도가 진행됩니다. (숫자가 클수록 최신 진도)
  - `study0`: 실습 없이 이론만 (FastAPI 기초이론 — ASGI, Pydantic, Django와 비교 등 선행 지식)
  - `study1` ~ `study5`: FastAPI 기본기 실습 (설치/실행, Path·Query·Pydantic 스키마, 의존성 주입과 라우터 분리, SQLAlchemy+DB 연동, 회원 모델)
  - `study6` ~ `study10`: 고급 기술 구현 (비동기 라우트, JWT 인증, CORS·예외 핸들러, 테스트코드, 설정 관리·페이지네이션)
  - `studyFinal`: 지금까지 배운 것을 합쳐 만드는 미니 게시판 API 프로젝트
- `demo/`: study1~study10 문서 내용을 단계별로 하나씩 실습하며 누적되는 FastAPI 프로젝트입니다. 커밋 히스토리를 따라가면 배운 순서 그대로 코드가 진화하는 것을 볼 수 있습니다.
- `project/`: `studyFinal.md`에 대응하는, `demo/`에서 익힌 개념을 전부 합쳐 처음부터 완성된 형태로 다시 설계한 완결된 미니 프로젝트(별도 FastAPI 프로젝트)입니다.

## 2. 작업 전 확인 사항

- 새 작업을 시작하기 전에 `studyN.md` 파일들을 번호 순서대로 확인하여 지금까지의 학습 진도와 맥락을 파악합니다.
- `demo/`, `project/` 프로젝트 코드가 study 문서 설명과 어긋나지 않는지 확인합니다.
- 새 studyN.md 문서를 추가/수정할 때는 이전 study 문서와 이어지는 흐름을 유지합니다.
- FastAPI 프로젝트(`demo/`, `project/`)는 각자 독립된 가상환경(`.venv`)과 `requirements.txt`를 가집니다. 두 `.venv` 모두 `.gitignore`에 의해 커밋 대상에서 제외됩니다 (SQLite DB 파일도 마찬가지).
- 모델(SQLAlchemy)을 변경했다면 실제로 테이블이 재생성되는지 확인하고, 가능하면 `uvicorn`으로 서버를 띄워 `curl`/`/docs`로 실제 동작을 확인한 뒤 커밋합니다.

## 3. 커밋 규칙

- 커밋 관련 규칙은 [COMMIT_GUIDE.md](./COMMIT_GUIDE.md) 문서를 따릅니다.

## 4. 언어 규칙

- 문서 내용, 커밋 설명: 한글
- 커밋 타입(prefix), 코드, 식별자, 파일명: 영어

## 5. 에이전트별 문서

- Claude: [.claude/CLAUDE.md](../.claude/CLAUDE.md)
- Grok: [.grok/GROK.md](../.grok/GROK.md)
- Codex: [.codex/AGENTS.md](../.codex/AGENTS.md)

## 6. 인수인계 원칙

- 작업을 마칠 때는 다음 에이전트/세션이 이어받을 수 있도록 변경 내용과 다음 단계 후보를 간단히 남깁니다.
- 불확실한 결정은 추측하지 말고 study 문서 내용과 [Notion 학습 목표 페이지](https://app.notion.com/p/FastAPI-3d6d7dec5e2e810fb6f5fa9e53bcb9a2)를 근거로 삼습니다.
- 이 문서나 커밋 가이드에 없는 새로운 컨벤션이 필요해지면, 추측해서 각자 다르게 처리하지 말고 이 문서를 먼저 갱신합니다.
