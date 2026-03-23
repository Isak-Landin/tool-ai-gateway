from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from repository_tools import (
    build_ripgrep_ignore_args,
    get_repository_ignore_patterns,
    get_repository_relative_path,
    is_ignored_repository_path,
    resolve_repository_target,
)


def search_repository_text(
    repo_path: str,
    query: str,
    relative_repo_path: str | None = None,
    case_sensitive: bool = False,
    max_results: int = 100,
) -> list[dict]:
    if not str(query).strip():
        raise ValueError("query is required")
    if max_results < 1:
        raise ValueError("max_results must be >= 1")

    repo_root, target_path = resolve_repository_target(
        repo_path=repo_path,
        relative_repo_path=relative_repo_path,
    )

    rg_path = shutil.which("rg")
    if rg_path is None:
        raise ValueError("ripgrep (rg) is required")

    ignored_path_patterns = get_repository_ignore_patterns()
    relative_target_path = get_repository_relative_path(repo_root, target_path)
    if is_ignored_repository_path(relative_target_path, ignored_path_patterns):
        raise ValueError(f"Path is excluded by configured ignore paths: {relative_target_path}")

    target_argument = "." if target_path == repo_root else target_path.relative_to(repo_root).as_posix()

    command = [
        rg_path,
        "--line-number",
        "--with-filename",
        "--color",
        "never",
    ]
    if not case_sensitive:
        command.append("-i")

    command.extend(build_ripgrep_ignore_args(ignored_path_patterns))
    command.append(query)
    command.append(target_argument)

    completed = subprocess.run(
        command,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    if completed.returncode not in {0, 1}:
        raise ValueError(completed.stderr.strip() or completed.stdout.strip() or "ripgrep failed")

    results: list[dict] = []
    for output_line in completed.stdout.splitlines():
        path_part, separator, remainder = output_line.partition(":")
        if not separator:
            continue

        line_number_part, separator, line_text = remainder.partition(":")
        if not separator:
            continue

        result_path = Path(path_part)
        if not result_path.is_absolute():
            result_path = (repo_root / result_path).resolve()
        else:
            result_path = result_path.resolve()
        try:
            relative_result_path = get_repository_relative_path(repo_root, result_path)
        except ValueError:
            relative_result_path = path_part

        try:
            line_number = int(line_number_part)
        except ValueError:
            continue

        results.append(
            {
                "path": relative_result_path,
                "line_number": line_number,
                "line_text": line_text,
            }
        )

        if len(results) >= max_results:
            break

    return results
