# Mini Board API

studyFinal의 FastAPI 앱이다. 실행과 경로 설명은 저장소 루트 [README.md](../README.md)와 [studyFinal.md](../studyFinal.md)에 있다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
pytest -q
```

화면은 `frontend/`에서 `npm run dev`로 켠다. 기본 API 주소는 `http://127.0.0.1:8000`이다.
