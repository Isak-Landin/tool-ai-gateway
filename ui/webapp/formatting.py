from __future__ import annotations

from datetime import datetime, timezone


def format_timestamp(value: str | None) -> str:
    """Return a readable timestamp for UI templates."""
    if not value:
        return "Unknown date"

    normalized_value = str(value).strip()
    if not normalized_value:
        return "Unknown date"

    try:
        parsed = datetime.fromisoformat(normalized_value.replace("Z", "+00:00"))
    except ValueError:
        return "Unknown date"

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone().strftime("%b %d, %Y %H:%M")
