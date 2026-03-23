from __future__ import annotations

from collections.abc import Iterable

from ollama.tool_module import OllamaToolModule


_REGISTERED_TOOL_MODULES: dict[str, OllamaToolModule] = {}
_DEFAULT_MODULES_LOADED = False


def register_tool(tool: OllamaToolModule) -> None:
    existing = _REGISTERED_TOOL_MODULES.get(tool.name)
    if existing is not None and existing != tool:
        raise ValueError(f"Ollama tool module '{tool.name}' is already registered")

    _REGISTERED_TOOL_MODULES[tool.name] = tool


def ensure_default_tool_modules_loaded() -> None:
    global _DEFAULT_MODULES_LOADED

    if _DEFAULT_MODULES_LOADED:
        return

    import ollama.tool_modules  # noqa: F401

    _DEFAULT_MODULES_LOADED = True


def get_registered_tool(name: str) -> OllamaToolModule:
    ensure_default_tool_modules_loaded()

    tool = _REGISTERED_TOOL_MODULES.get(name)
    if tool is None:
        raise ValueError(f"Unknown Ollama tool module: {name}")

    return tool


def list_registered_tools() -> list[OllamaToolModule]:
    ensure_default_tool_modules_loaded()
    return list(_REGISTERED_TOOL_MODULES.values())


def resolve_registered_tools(tool_names: str | Iterable[str] | None = None) -> list[OllamaToolModule]:
    if tool_names is None:
        return []

    ensure_default_tool_modules_loaded()

    names = [tool_names] if isinstance(tool_names, str) else list(tool_names)
    return [get_registered_tool(name) for name in names]


def build_tool_schemas(tool_names: str | Iterable[str] | None = None) -> list[dict]:
    return [tool.build_schema() for tool in resolve_registered_tools(tool_names)]


def build_tool_prompt_fragment(tool_names: str | Iterable[str] | None = None) -> str | None:
    fragments = [
        fragment
        for tool in resolve_registered_tools(tool_names)
        if (fragment := tool.build_prompt_fragment()) is not None
    ]

    if not fragments:
        return None

    return "\n\n".join(fragments)
