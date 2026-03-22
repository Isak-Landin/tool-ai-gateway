from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class OllamaToolModule:
    name: str
    schema: dict[str, Any]
    prompt_fragment: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema.get("type") != "function":
            raise ValueError(f"Ollama tool module '{self.name}' must use schema type 'function'")

        function_data = self.schema.get("function") or {}
        schema_name = function_data.get("name")
        if schema_name != self.name:
            raise ValueError(
                f"Ollama tool module name '{self.name}' does not match schema function name '{schema_name}'"
            )

        parameters = function_data.get("parameters") or {}
        if parameters.get("type") != "object":
            raise ValueError(
                f"Ollama tool module '{self.name}' must declare function parameters as an object schema"
            )

    def build_schema(self) -> dict[str, Any]:
        return deepcopy(self.schema)

    def build_prompt_fragment(self) -> str | None:
        if self.prompt_fragment is None:
            return None

        fragment = self.prompt_fragment.strip()
        return fragment or None
