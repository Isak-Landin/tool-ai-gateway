"""
Internal rules for file-runtime function helpers.

Ownership:
- This file owns higher-level live file/search behavior that composes caller-
  supplied repository and persistence dependencies into route-usable and
  execution-usable file operations.
- This file owns file-specific validation, ignore-path enforcement, and
  file-runtime-shaped error translation.
- This file does not own repository runtime construction, branch selection
  policy, or file-row persistence internals.

Rule-set split:
- Internal helper rules apply to shared validation and dependency/error
  translation helpers used by file operations.
- Encapsulated/public helper rules apply to exposed file use-case functions.

Internal helper rules:
- Public file functions must validate caller-supplied runtime inputs before
- delegating to lower helpers.
- Public file functions must require explicit dependencies through internal
  helper functions instead of creating or discovering them.
- Lower git/persistence failures must be translated into `FileRuntimeError`.

Encapsulated/public helper rules:
- File-read and search helpers should keep caller policy explicit through
  parameters such as `branch`, `relative_repo_path`, `start_line`,
  `number_of_lines`, `end_line`, `case_sensitive`, and `max_results`.
- `read_file(...)`, `search_text(...)`, `list_persisted_files(...)`,
  `get_persisted_file(...)`, and `persist_file_snapshot(...)` are the current
  file-runtime use-case surface and should compose only the declared internal
  helper rules plus the lower owned helpers they target.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from errors import FileRuntimeError, RepositoryFilePersistenceError
from repository_runtime.git import run_git_probe
from repository_tools import (
    get_repository_ignore_patterns,
    is_ignored_repository_path,
    normalize_repository_relative_path,
)


def _require_repository_runtime(repository_runtime):
    if repository_runtime is None:
        raise FileRuntimeError("repository_runtime is required")

    return repository_runtime


def _require_branch(branch: str | None) -> str:
    normalized_branch = str(branch or "").strip()
    if not normalized_branch:
        raise FileRuntimeError("branch is required")

    return normalized_branch


def _require_files_repository(files_repository):
    if files_repository is None:
        raise FileRuntimeError("files_repository is required for persistence-backed file operations")

    return files_repository


def _get_ignore_patterns() -> list[str]:
    return list(get_repository_ignore_patterns())


def get_ignore_patterns() -> list[str]:
    return _get_ignore_patterns()


def _normalize_relative_repo_path(relative_repo_path: str | None = None, *, allow_root: bool) -> str:
    try:
        return normalize_repository_relative_path(relative_repo_path, allow_root=allow_root)
    except ValueError as e:
        raise FileRuntimeError(str(e)) from e


def _assert_not_ignored(normalized_relative_path: str) -> None:
    if is_ignored_repository_path(normalized_relative_path, _get_ignore_patterns()):
        raise FileRuntimeError(f"Path is excluded by configured ignore paths: {normalized_relative_path}")


def _run_read_only_git(repository_runtime, args: list[str]) -> tuple[int, str]:
    required_repository_runtime = _require_repository_runtime(repository_runtime)
    return run_git_probe(
        required_repository_runtime.shell,
        args,
    )


def read_file(
    repository_runtime,
    *,
    branch: str,
    relative_repo_path: str,
    start_line: int | None = None,
    number_of_lines: int | None = None,
    end_line: int | None = None,
) -> dict:
    if number_of_lines is not None and end_line is not None:
        raise FileRuntimeError("Use either number_of_lines or end_line, not both")

    required_branch = _require_branch(branch)
    normalized_relative_path = _normalize_relative_repo_path(relative_repo_path, allow_root=False)
    _assert_not_ignored(normalized_relative_path)

    effective_start_line = 1 if start_line is None else start_line
    if effective_start_line < 1:
        raise FileRuntimeError("start_line must be >= 1")
    if number_of_lines is not None and number_of_lines < 1:
        raise FileRuntimeError("number_of_lines must be >= 1")
    if end_line is not None and end_line < effective_start_line:
        raise FileRuntimeError("end_line must be >= start_line")

    git_relative_path = normalized_relative_path.lstrip("/")
    file_code, file_content = _run_read_only_git(
        repository_runtime,
        ["show", f"{required_branch}:{git_relative_path}"],
    )
    if file_code != 0:
        raise FileRuntimeError(file_content or f"Failed to read file from branch {required_branch}")

    all_lines = file_content.splitlines()
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
        "name": PurePosixPath(git_relative_path).name,
        "path": normalized_relative_path,
        "content": "\n".join(content_lines),
        "start_line": effective_start_line,
        "end_line": effective_end_line,
        "total_lines": total_lines,
    }


def search_text(
    repository_runtime,
    *,
    branch: str,
    query: str,
    relative_repo_path: str | None = None,
    case_sensitive: bool = False,
    max_results: int = 100,
) -> list[dict]:
    if not str(query).strip():
        raise FileRuntimeError("query is required")
    if max_results < 1:
        raise FileRuntimeError("max_results must be >= 1")

    required_branch = _require_branch(branch)
    normalized_relative_path = _normalize_relative_repo_path(relative_repo_path, allow_root=True)
    _assert_not_ignored(normalized_relative_path)

    git_args = ["grep", "-n", "--full-name", "--color=never"]
    if not case_sensitive:
        git_args.append("-i")
    git_args.extend(["-e", query, required_branch])

    git_relative_path = normalized_relative_path.lstrip("/")
    if git_relative_path:
        git_args.extend(["--", git_relative_path])

    grep_code, output = _run_read_only_git(
        repository_runtime,
        git_args,
    )
    if grep_code != 0 and output:
        raise FileRuntimeError(output)

    search_results: list[dict] = []
    for output_line in output.splitlines():
        treeish_part, separator, remainder = output_line.partition(":")
        if not separator or treeish_part != required_branch:
            continue

        path_part, separator, remainder = remainder.partition(":")
        if not separator:
            continue

        line_number_part, separator, line_text = remainder.partition(":")
        if not separator:
            continue

        normalized_result_path = "/" + path_part.lstrip("/")
        if is_ignored_repository_path(normalized_result_path, _get_ignore_patterns()):
            continue

        try:
            line_number = int(line_number_part)
        except ValueError:
            continue

        search_results.append(
            {
                "path": normalized_result_path,
                "line_number": line_number,
                "line_text": line_text,
            }
        )
        if len(search_results) >= max_results:
            break

    return search_results


def list_persisted_files(files_repository) -> list[dict]:
    required_files_repository = _require_files_repository(files_repository)
    try:
        return required_files_repository.list_file_rows()
    except RepositoryFilePersistenceError as e:
        raise FileRuntimeError(str(e)) from e


def get_persisted_file(files_repository, relative_repo_path: str) -> dict | None:
    required_files_repository = _require_files_repository(files_repository)
    try:
        return required_files_repository.get_file_row_by_path(relative_repo_path)
    except RepositoryFilePersistenceError as e:
        raise FileRuntimeError(str(e)) from e


def persist_file_snapshot(
    repository_runtime,
    files_repository,
    *,
    branch: str,
    relative_repo_path: str,
) -> dict:
    live_file = read_file(
        repository_runtime,
        branch=branch,
        relative_repo_path=relative_repo_path,
    )
    required_files_repository = _require_files_repository(files_repository)
    try:
        return required_files_repository.upsert_file_row(
            relative_repo_path=live_file["path"],
            name=live_file["name"],
            content=live_file["content"],
            total_lines=live_file["total_lines"],
        )
    except RepositoryFilePersistenceError as e:
        raise FileRuntimeError(str(e)) from e


# Questionable methods intentionally left out for now:
# - list_tree(...): questionable because the behavior is deep and likely needed, but its
#   current encapsulation may span multiple owners and should be reintroduced only after the
#   lower ownership split is clarified.
# - load_selected_context(...): questionable because it appears execution-shaped rather than
#   generally file-serving shaped, so its long-term owner should be confirmed before return.
