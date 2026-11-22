"""문서 인덱스를 메모리에 두고 질문과 스트리밍 답을 제공한다."""

import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import Field

from app.ai_engine import answer_from_hits, chunk_text, complete, relevant_chunks
from app.errors import AppError
from app.schemas.common import APIModel

router = APIRouter(prefix="/ai", tags=["ai"])
_documents: dict[str, list[str]] = {}


class DocumentIn(APIModel):
    document_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1)


class AskIn(APIModel):
    document_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=500)


def reset_documents() -> None:
    _documents.clear()


def _hits_or_404(document_id: str, question: str) -> list[dict]:
    chunks = _documents.get(document_id)
    if chunks is None:
        raise AppError(
            404,
            "NOT_FOUND",
            "해당 문서의 인덱스를 찾을 수 없습니다. 문서를 다시 업로드해 주세요.",
        )
    return relevant_chunks(chunks, question)


@router.post("/documents", status_code=201)
def index_document(payload: DocumentIn):
    chunks = chunk_text(payload.text)
    _documents[payload.document_id] = chunks
    return {"data": {"documentId": payload.document_id, "chunks": len(chunks)}}


@router.post("/ask")
async def ask(payload: AskIn):
    hits = _hits_or_404(payload.document_id, payload.question)
    try:
        answer, model = await complete(payload.question, hits)
    except Exception as exc:
        raise AppError(503, "INTERNAL", f"AI 모델 호출 실패: {exc}") from exc
    return {
        "data": {
            "documentId": payload.document_id,
            "question": payload.question,
            "answer": answer,
            "sources": hits,
            "model": model,
        }
    }


@router.get("/ask/stream")
async def ask_stream(
    document_id: str = Query(alias="documentId", min_length=1),
    question: str = Query(min_length=1),
):
    hits = _hits_or_404(document_id, question)
    answer = answer_from_hits(hits)

    async def events():
        for part in answer.split(" "):
            yield f"data: {json.dumps({'text': part}, ensure_ascii=False)}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
