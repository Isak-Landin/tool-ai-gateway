from __future__ import annotations

from pathlib import Path

from repository_tools import (
    get_repository_ignore_patterns,
    get_repository_relative_path,
    get_repository_shell_target_argument,
    is_ignored_repository_path,
    quote_shell_args,
    resolve_repository_target,
)


def _build_tree_entry(repo_root: Path, target_path: Path, base_path: Path) -> dict:
    return {
        "name": target_path.name or repo_root.name,
        "path": get_repository_relative_path(repo_root, target_path),
        "is_dir": target_path.is_dir(),
        "is_file": target_path.is_file(),
        "depth": len(target_path.relative_to(base_path).parts),
    }


def list_repository_tree(shell_executor, repo_path: str, relative_repo_path: str | None = None) -> list[dict]:
    repo_root, target_path = resolve_repository_target(
        repo_path=repo_path,
        relative_repo_path=relative_repo_path,
    )
    ignored_path_patterns = get_repository_ignore_patterns()
    relative_target_path = get_repository_relative_path(repo_root, target_path)
    if is_ignored_repository_path(relative_target_path, ignored_path_patterns):
        raise ValueError(f"Path is excluded by configured ignore paths: {relative_target_path}")

    if not target_path.is_dir():
        raise ValueError(f"Path is not a directory in repository: {get_repository_relative_path(repo_root, target_path)}")

    shell_target_argument = get_repository_shell_target_argument(repo_root, target_path)
    find_command = quote_shell_args(["find", shell_target_argument, "-mindepth", "1", "-print"])
    return_code, output = shell_executor.run(find_command)
    if return_code != 0:
        raise ValueError(output.strip() or "find failed")

    collected_entries: list[dict] = []
    for output_line in output.splitlines():
        normalized_output_line = output_line.strip()
        if not normalized_output_line:
            continue

        if normalized_output_line == ".":
            resolved_path = repo_root
        else:
            resolved_path = (repo_root / normalized_output_line.lstrip("./")).resolve()

        try:
            relative_entry_path = get_repository_relative_path(repo_root, resolved_path)
        except ValueError:
            continue

        if is_ignored_repository_path(relative_entry_path, ignored_path_patterns):
            continue

        collected_entries.append(
            _build_tree_entry(
                repo_root=repo_root,
                target_path=resolved_path,
                base_path=target_path,
            )
        )

    return collected_entries
