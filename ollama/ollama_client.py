import requests

from ollama.config import (
    get_default_chat_request_fields,
    get_ollama_base_url,
)


def send_chat_envelope(chat_envelope: dict) -> dict:
    payload = dict(chat_envelope)
    default_fields = get_default_chat_request_fields()

    payload.setdefault("stream", default_fields.get("stream"))

    default_options = default_fields.get("options") or {}
    payload_options = dict(payload.get("options") or {})
    for option_name, option_value in default_options.items():
        payload_options.setdefault(option_name, option_value)
    if payload_options:
        payload["options"] = payload_options

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
        "role": message.get("role"),
        "content": message.get("content"),
        "thinking": message.get("thinking"),
        "tool_calls": message.get("tool_calls") or [],
        "tool_name": message.get("tool_name"),
        "images": message.get("images"),
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
