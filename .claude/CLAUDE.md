# Claude 전용 인수인계 문서

공통 규칙은 [../.agent/AGENTS.md](../.agent/AGENTS.md) 및 [../.agent/COMMIT_GUIDE.md](../.agent/COMMIT_GUIDE.md)를 먼저 확인하고 따릅니다.
이 문서에는 Claude를 사용할 때만 해당하는 특이사항을 기록합니다.

## Claude 관련 참고 사항

- `manage.py shell -c "..."` 등으로 한글이 포함된 데이터를 `print`하면 Windows 콘솔 코드페이지(CP949) 문제로 `UnicodeEncodeError`가 발생하거나 글자가 깨져(mojibake) 보일 수 있습니다. `PYTHONUTF8=1` 환경변수를 붙여 실행하면 대부분 해결되며, 그래도 글자가 깨져 보이는 것은 터미널 표시 문제일 뿐 실제 DB 데이터는 정상입니다.
- Git Bash의 `/tmp`는 Git Bash 자체의 가상 경로이며, `.venv/Scripts/python.exe`(네이티브 Windows Python)는 이 경로를 직접 읽지 못할 수 있습니다. curl 등으로 `/tmp`에 저장한 파일을 Python으로 다시 읽어야 한다면, bash 안에서 `grep`/`sed`로 필요한 값만 추출하거나 Windows 경로를 사용합니다.
- curl로 한글이 포함된 JSON body(`-d '{"title":"한글", ...}'`)를 보낼 때 Windows 터미널 코드페이지 문제로 인코딩이 깨질 수 있습니다. 동작 검증용 smoke test에는 영어 payload를 사용하고, 실제 한글 데이터 검증은 브라우저나 `manage.py shell`에서 직접 진행하는 것이 안전합니다.
