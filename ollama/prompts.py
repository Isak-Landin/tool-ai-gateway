from collections.abc import Iterable
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = BASE_DIR / "system" / "system.txt"


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def build_system_prompt(system_prompt: str | None = None) -> str:
    if system_prompt is not None:
        return system_prompt.strip()

    return load_system_prompt()


def build_system_message(system_prompt: str | None = None) -> dict:
    return {
        "role": "system",
        "content": build_system_prompt(system_prompt=system_prompt),
    }


def merge_system_prompt_fragments(
    base_system_prompt: str | None,
    extra_fragments: str | Iterable[str] | None,
) -> str | None:
    if extra_fragments is None:
        return base_system_prompt

    fragments = [extra_fragments] if isinstance(extra_fragments, str) else list(extra_fragments)
    normalized_fragments = [fragment.strip() for fragment in fragments if fragment and fragment.strip()]
    if not normalized_fragments:
        return base_system_prompt

    merged_fragment = "\n\n".join(normalized_fragments)

    if base_system_prompt is None:
        return build_system_prompt() + "\n\n" + merged_fragment

    stripped_base = base_system_prompt.strip()
    if not stripped_base:
        return merged_fragment

    return stripped_base + "\n\n" + merged_fragment
