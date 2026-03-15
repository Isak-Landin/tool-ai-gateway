import os

import requests

from ollama.builder import build_chat_payload


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "seamon67/Ministral-3-Reasoning:14b")


def call_ollama(user_message: str, history: list[dict] | None = None) -> dict:
    payload = build_chat_payload(
        model=OLLAMA_MODEL,
        user_message=user_message,
        history=history,
    )

    # MVP uses non-streaming final-body handling.
    # Native Ollama streaming requires chunk accumulation for content/thinking/tool_calls.
    payload.setdefault("stream", False)

    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=300,
    )

    if not r.ok:
        print("OLLAMA STATUS:", r.status_code, flush=True)
        print("OLLAMA BODY:", r.text, flush=True)
        r.raise_for_status()

    return r.json()


def parse_model_output(data: dict) -> dict:
    message = data.get("message") or {}

    return {
        "message": message,
        "content": message.get("content") or "",
        "thinking": message.get("thinking") or "",
        "tool_calls": message.get("tool_calls") or [],
        "done": data.get("done"),
        "done_reason": data.get("done_reason"),
        "raw_response": data,
    }