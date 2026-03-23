from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


def _normalize_names(names: str | Iterable[str] | None = None) -> list[str]:
    if names is None:
        return []

    values = [names] if isinstance(names, str) else list(names)
    return [value for value in values if str(value).strip()]


def _merge_unique_names(names: Iterable[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for name in names:
        if name not in seen:
            merged.append(name)
            seen.add(name)

    return merged


@dataclass(frozen=True, slots=True)
class OllamaSpecPart:
    name: str
    tool_names: tuple[str, ...] = ()
    prompt_fragment: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def build_prompt_fragment(self) -> str | None:
        if self.prompt_fragment is None:
            return None

        fragment = self.prompt_fragment.strip()
        return fragment or None


@dataclass(frozen=True, slots=True)
class OllamaChatSpec:
    name: str
    part_names: tuple[str, ...] = ()
    tool_names: tuple[str, ...] = ()
    prompt_fragments: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def build_prompt_fragments(self) -> list[str]:
        return [fragment.strip() for fragment in self.prompt_fragments if fragment and fragment.strip()]


_REGISTERED_SPEC_PARTS: dict[str, OllamaSpecPart] = {}
_REGISTERED_CHAT_SPECS: dict[str, OllamaChatSpec] = {}


def register_spec_part(part: OllamaSpecPart) -> None:
    existing = _REGISTERED_SPEC_PARTS.get(part.name)
    if existing is not None and existing != part:
        raise ValueError(f"Ollama spec part '{part.name}' is already registered")

    _REGISTERED_SPEC_PARTS[part.name] = part


def register_chat_spec(spec: OllamaChatSpec) -> None:
    existing = _REGISTERED_CHAT_SPECS.get(spec.name)
    if existing is not None and existing != spec:
        raise ValueError(f"Ollama chat spec '{spec.name}' is already registered")

    _REGISTERED_CHAT_SPECS[spec.name] = spec


def get_spec_part(name: str) -> OllamaSpecPart:
    part = _REGISTERED_SPEC_PARTS.get(name)
    if part is None:
        raise ValueError(f"Unknown Ollama spec part: {name}")

    return part


def get_chat_spec(name: str) -> OllamaChatSpec:
    spec = _REGISTERED_CHAT_SPECS.get(name)
    if spec is None:
        raise ValueError(f"Unknown Ollama chat spec: {name}")

    return spec


def list_spec_parts() -> list[OllamaSpecPart]:
    return list(_REGISTERED_SPEC_PARTS.values())


def list_chat_specs() -> list[OllamaChatSpec]:
    return list(_REGISTERED_CHAT_SPECS.values())


def resolve_spec_parts(part_names: str | Iterable[str] | None = None) -> list[OllamaSpecPart]:
    return [get_spec_part(name) for name in _normalize_names(part_names)]


def resolve_chat_specs(spec_names: str | Iterable[str] | None = None) -> list[OllamaChatSpec]:
    return [get_chat_spec(name) for name in _normalize_names(spec_names)]


def build_spec_tool_names(
    spec_names: str | Iterable[str] | None = None,
    part_names: str | Iterable[str] | None = None,
) -> list[str]:
    merged_names: list[str] = []

    for spec in resolve_chat_specs(spec_names):
        merged_names.extend(spec.tool_names)
        for part in resolve_spec_parts(spec.part_names):
            merged_names.extend(part.tool_names)

    for part in resolve_spec_parts(part_names):
        merged_names.extend(part.tool_names)

    return _merge_unique_names(merged_names)


def build_spec_prompt_fragments(
    spec_names: str | Iterable[str] | None = None,
    part_names: str | Iterable[str] | None = None,
) -> list[str]:
    fragments: list[str] = []

    for spec in resolve_chat_specs(spec_names):
        fragments.extend(spec.build_prompt_fragments())
        for part in resolve_spec_parts(spec.part_names):
            if (fragment := part.build_prompt_fragment()) is not None:
                fragments.append(fragment)

    for part in resolve_spec_parts(part_names):
        if (fragment := part.build_prompt_fragment()) is not None:
            fragments.append(fragment)

    return fragments
