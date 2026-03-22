import requests

from ollama.builder import build_chat_payload
from ollama.config import get_ollama_base_url, get_ollama_default_model


def call_ollama(
    user_message: str | None = None,
    history: list[dict] | None = None,
    *,
    messages: list[dict] | None = None,
    model: str | None = None,
    system_prompt: str | None = None,
    tool_name: str | None = None,
) -> dict:
    payload = build_chat_payload(
        model=model or get_ollama_default_model(),
        user_message=user_message,
        history=history,
        messages=messages,
        system_prompt=system_prompt,
        tool_name=tool_name,
    )

    # MVP uses non-streaming final-body handling.
    # Native Ollama streaming requires chunk accumulation for content/thinking/tool_calls.
    payload.setdefault("stream", False)

    r = requests.post(
        f"{get_ollama_base_url()}/api/chat",
        json=payload,
        timeout=300,
    )

    if not r.ok:

        r.raise_for_status()

    return r.json()


def parse_model_output(data: dict) -> dict:
    message = data.get("message") or {}

    return {
        "model": data.get("model"),
        "created_at": data.get("created_at"),
        "message": message,
        "content": message.get("content"),
        "thinking": message.get("thinking"),
        "tool_calls": message.get("tool_calls") or [],
        "done": data.get("done"),
        "done_reason": data.get("done_reason"),
        "total_duration": data.get("total_duration"),
        "load_duration": data.get("load_duration"),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "prompt_eval_duration": data.get("prompt_eval_duration"),
        "eval_count": data.get("eval_count"),
        "eval_duration": data.get("eval_duration"),
        "raw_response": data,
    }
