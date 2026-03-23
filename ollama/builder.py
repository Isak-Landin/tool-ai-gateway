from __future__ import annotations

from ollama.prompts import build_system_message


def build_chat_message(
    role: str,
    content: str | None = None,
    *,
    tool_calls: list[dict] | None = None,
    tool_name: str | None = None,
    images: list[str] | None = None,
    thinking: str | None = None,
) -> dict:
    if role not in {"system", "user", "assistant", "tool"}:
        raise ValueError(f"Unsupported chat message role: {role}")

    message = {"role": role}

    if content is not None:
        message["content"] = content
    if tool_calls is not None:
        message["tool_calls"] = list(tool_calls)
    if tool_name is not None:
        message["tool_name"] = tool_name
    if images is not None:
        message["images"] = list(images)
    if thinking is not None:
        message["thinking"] = thinking

    return message


def create_chat_envelope(
    model: str,
    *,
    messages: list[dict] | None = None,
    tools: list[dict] | None = None,
    stream: bool | None = None,
    options: dict | None = None,
    format: str | dict | None = None,
    keep_alive: str | int | None = None,
    think: bool | None = None,
) -> dict:
    envelope = {
        "model": model,
        "messages": list(messages or []),
    }

    return merge_chat_envelope_fields(
        envelope,
        tools=list(tools) if tools else None,
        stream=stream,
        options=dict(options) if options else None,
        format=format,
        keep_alive=keep_alive,
        think=think,
    )


def merge_chat_envelope_fields(chat_envelope: dict, **fields: object) -> dict:
    for field_name, field_value in fields.items():
        if field_value is not None:
            chat_envelope[field_name] = field_value

    return chat_envelope


def append_chat_message(chat_envelope: dict, message: dict) -> dict:
    chat_envelope.setdefault("messages", []).append(dict(message))
    return chat_envelope


def append_system_message(chat_envelope: dict, system_prompt: str | None = None) -> dict:
    return append_chat_message(
        chat_envelope,
        build_system_message(system_prompt=system_prompt),
    )


def append_user_message(chat_envelope: dict, content: str) -> dict:
    return append_chat_message(chat_envelope, build_chat_message(role="user", content=content))


def append_assistant_message(
    chat_envelope: dict,
    content: str | None = None,
    *,
    tool_calls: list[dict] | None = None,
    tool_name: str | None = None,
    images: list[str] | None = None,
    thinking: str | None = None,
) -> dict:
    effective_content = content
    if effective_content is None and tool_calls is not None:
        effective_content = ""

    return append_chat_message(
        chat_envelope,
        build_chat_message(
            role="assistant",
            content=effective_content,
            tool_calls=tool_calls,
            tool_name=tool_name,
            images=images,
            thinking=thinking,
        ),
    )


def append_tool_message(chat_envelope: dict, content: str, tool_name: str) -> dict:
    return append_chat_message(
        chat_envelope,
        build_chat_message(role="tool", content=content, tool_name=tool_name),
    )
