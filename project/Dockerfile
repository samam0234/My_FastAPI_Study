FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV DATABASE_URL=sqlite:///./demo.db
EXPOSE 8000

# 컨테이너 안에서는 127.0.0.1에만 묶으면 호스트에서 접속할 수 없다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
