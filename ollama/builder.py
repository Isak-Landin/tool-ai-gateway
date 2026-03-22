from ollama.config import get_default_chat_options
from ollama.prompts import build_system_message, merge_system_prompt_fragments
from ollama.tool_registry import build_tool_prompt_fragment, build_tool_schemas


def build_messages(
    user_message: str | None = None,
    history: list[dict] | None = None,
    messages: list[dict] | None = None,
    system_prompt: str | None = None,
) -> list[dict]:
    if messages is not None:
        if user_message is not None or history is not None:
            raise ValueError("Use either messages or user_message/history, not both")
        return list(messages)

    if user_message is None or not str(user_message).strip():
        raise ValueError("user_message is required when messages is not provided")

    built_messages = [build_system_message(system_prompt=system_prompt)]

    if history:
        built_messages.extend(history)

    built_messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    return built_messages


def build_chat_payload(
    model: str,
    user_message: str | None = None,
    history: list[dict] | None = None,
    messages: list[dict] | None = None,
    system_prompt: str | None = None,
    tool_name: str | None = None,
) -> dict:
    effective_system_prompt = merge_system_prompt_fragments(
        base_system_prompt=system_prompt,
        extra_fragment=build_tool_prompt_fragment(tool_name),
    )

    payload = {
        "model": model,
        "messages": build_messages(
            user_message=user_message,
            history=history,
            messages=messages,
            system_prompt=effective_system_prompt,
        ),
    }

    payload.update(get_default_chat_options())

    tools = build_tool_schemas(tool_name)
    if tools:
        payload["tools"] = tools

    return payload
