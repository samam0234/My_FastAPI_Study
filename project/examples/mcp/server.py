"""문서 발췌로만 답하는 최소 MCP 도구.

프로젝트 폴더에서 실행한다.

    python examples/mcp/server.py

한 줄에 JSON-RPC 하나를 넣고 Enter. 예시 요청은 파일 아래 주석을 본다.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.ai_engine import answer_from_hits, chunk_text, relevant_chunks


def ask_document(text: str, question: str) -> str:
    hits = relevant_chunks(chunk_text(text), question)
    return answer_from_hits(hits)


def handle(message: dict) -> dict:
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        result = {"protocolVersion": "2024-11-05", "serverInfo": {"name": "board-ask", "version": "0.1.0"}}
    elif method == "tools/list":
        result = {
            "tools": [
                {
                    "name": "ask_document",
                    "description": "주어진 문서 텍스트 안에서만 질문에 답한다.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}, "question": {"type": "string"}},
                        "required": ["text", "question"],
                    },
                }
            ]
        }
    elif method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") != "ask_document":
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown tool"}}
        arguments = params.get("arguments") or {}
        answer = ask_document(str(arguments.get("text", "")), str(arguments.get("question", "")))
        result = {"content": [{"type": "text", "text": answer}]}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown method"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = handle(json.loads(line))
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

# {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ask_document","arguments":{"text":"FastAPI는 타입으로 검증한다.","question":"타입"}}}
