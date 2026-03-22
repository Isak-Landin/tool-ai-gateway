from __future__ import annotations

from collections.abc import Iterable

from ollama.tool_module import OllamaToolModule


_REGISTERED_TOOL_MODULES: dict[str, OllamaToolModule] = {}
_DEFAULT_MODULES_LOADED = False


def register_tool_module(module: OllamaToolModule) -> None:
    existing = _REGISTERED_TOOL_MODULES.get(module.name)
    if existing is not None and existing != module:
        raise ValueError(f"Ollama tool module '{module.name}' is already registered")

    _REGISTERED_TOOL_MODULES[module.name] = module


def ensure_default_tool_modules_loaded() -> None:
    global _DEFAULT_MODULES_LOADED

    if _DEFAULT_MODULES_LOADED:
        return

    import ollama.tool_modules  # noqa: F401

    _DEFAULT_MODULES_LOADED = True


def get_tool_module(name: str) -> OllamaToolModule:
    ensure_default_tool_modules_loaded()

    module = _REGISTERED_TOOL_MODULES.get(name)
    if module is None:
        raise ValueError(f"Unknown Ollama tool module: {name}")

    return module


def list_tool_modules() -> list[OllamaToolModule]:
    ensure_default_tool_modules_loaded()
    return list(_REGISTERED_TOOL_MODULES.values())


def resolve_tool_modules(tool_names: str | Iterable[str] | None = None) -> list[OllamaToolModule]:
    if tool_names is None:
        return []

    ensure_default_tool_modules_loaded()

    names = [tool_names] if isinstance(tool_names, str) else list(tool_names)
    return [get_tool_module(name) for name in names]


def build_tool_schemas(tool_names: str | Iterable[str] | None = None) -> list[dict]:
    return [module.build_schema() for module in resolve_tool_modules(tool_names)]


def build_tool_prompt_fragment(tool_names: str | Iterable[str] | None = None) -> str | None:
    fragments = [
        fragment
        for module in resolve_tool_modules(tool_names)
        if (fragment := module.build_prompt_fragment()) is not None
    ]

    if not fragments:
        return None

    return "\n\n".join(fragments)
