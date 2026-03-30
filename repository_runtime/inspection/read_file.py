from __future__ import annotations

from repository_tools import (
    get_repository_ignore_patterns,
    get_repository_relative_path,
    is_ignored_repository_path,
    resolve_repository_target,
)


def read_repository_file(
    repo_path: str,
    relative_repo_path: str,
    start_line: int | None = None,
    number_of_lines: int | None = None,
    end_line: int | None = None,
) -> dict:
    if number_of_lines is not None and end_line is not None:
        raise ValueError("Use either number_of_lines or end_line, not both")

    repo_root, target_path = resolve_repository_target(
        repo_path=repo_path,
        relative_repo_path=relative_repo_path,
    )

    relative_target_path = get_repository_relative_path(repo_root, target_path)
    ignored_path_patterns = get_repository_ignore_patterns()
    if is_ignored_repository_path(relative_target_path, ignored_path_patterns):
        raise ValueError(f"Path is excluded by configured ignore paths: {relative_target_path}")

    if not target_path.is_file():
        raise ValueError(f"Path is not a file in repository: {relative_target_path}")

    effective_start_line = 1 if start_line is None else start_line
    if effective_start_line < 1:
        raise ValueError("start_line must be >= 1")
    if number_of_lines is not None and number_of_lines < 1:
        raise ValueError("number_of_lines must be >= 1")
    if end_line is not None and end_line < effective_start_line:
        raise ValueError("end_line must be >= start_line")

    try:
        all_lines = target_path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise ValueError(str(e)) from e

    total_lines = len(all_lines)
    if number_of_lines is not None:
        effective_end_line = effective_start_line + number_of_lines - 1
    elif end_line is not None:
        effective_end_line = end_line
    else:
        effective_end_line = total_lines

    effective_end_line = min(effective_end_line, total_lines)
    content_lines = all_lines[effective_start_line - 1:effective_end_line]

    return {
        "name": target_path.name,
        "path": relative_target_path,
        "content": "\n".join(content_lines),
        "start_line": effective_start_line,
        "end_line": effective_end_line,
        "total_lines": total_lines,
    }
