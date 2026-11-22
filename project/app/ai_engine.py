"""문서 발췌만 근거로 답하는 작은 검색.

외부 모델을 호출하지 않아도 동작한다. 키가 있을 때만 OpenAI로 문장을 다듬는다.
"""

from __future__ import annotations

import os
import re

import httpx

from app.config import get_settings


def chunk_text(text: str, size: int = 180) -> list[str]:
    pieces = [text[index : index + size].strip() for index in range(0, len(text), size)]
    return [piece for piece in pieces if piece]


def _tokens(text: str) -> set[str]:
    words = set(re.findall(r"[0-9A-Za-z가-힣]{2,}", text.lower()))
    chars = re.sub(r"\s+", "", text)
    bigrams = {chars[i : i + 2] for i in range(len(chars) - 1)} if len(chars) > 1 else set()
    return words | bigrams


def relevant_chunks(chunks: list[str], question: str, top_k: int = 3) -> list[dict]:
    query_tokens = _tokens(question)
    scored: list[dict] = []
    for index, chunk in enumerate(chunks):
        overlap = _tokens(chunk) & query_tokens
        if not overlap:
            continue
        scored.append(
            {
                "chunkIndex": index,
                "text": chunk,
                "score": round(len(overlap) / max(len(query_tokens), 1), 4),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def answer_from_hits(hits: list[dict]) -> str:
    if not hits:
        return "찾을 수 없습니다"
    lines = [f"(발췌 {index}) {hit['text']}" for index, hit in enumerate(hits, start=1)]
    return "문서에서 찾은 내용입니다.\n" + "\n".join(lines)


def resolve_provider() -> str:
    """SocialForge에서 쓰던 선택 규칙. 키가 없으면 mock이라 네트워크를 타지 않는다."""
    settings = get_settings()
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider == "openai" and settings.openai_api_key:
        return "openai"
    if provider == "ollama":
        return "ollama"
    if not provider and settings.openai_api_key:
        return "openai"
    return "mock"


async def complete(question: str, hits: list[dict]) -> tuple[str, str]:
    provider = resolve_provider()
    fallback = answer_from_hits(hits)
    if provider == "mock" or not hits:
        model = "mock" if provider == "mock" else get_settings().ollama_model
        return fallback, model if provider != "mock" else "mock"
    settings = get_settings()
    if provider == "openai":
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "다음 발췌 안에서만 질문에 답하세요. JSON {\"answer\": \"...\"} 만 반환하세요.\n"
                                f"질문: {question}\n발췌:\n{fallback}"
                            ),
                        }
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        return content, "gpt-4o-mini"
    return fallback, settings.ollama_model
