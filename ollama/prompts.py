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
    extra_fragment: str | None,
) -> str | None:
    if extra_fragment is None:
        return base_system_prompt

    if base_system_prompt is None:
        return build_system_prompt() + "\n\n" + extra_fragment

    stripped_base = base_system_prompt.strip()
    if not stripped_base:
        return extra_fragment

    return stripped_base + "\n\n" + extra_fragment
