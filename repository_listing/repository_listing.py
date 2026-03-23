from __future__ import annotations

from pathlib import Path

from repository_tools import (
    get_repository_ignore_patterns,
    get_repository_relative_path,
    is_ignored_repository_path,
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


def _collect_tree_entries(
    repo_root: Path,
    current_path: Path,
    base_path: Path,
    ignored_path_patterns: list[str],
) -> list[dict]:
    collected_entries: list[dict] = []

    for entry in sorted(current_path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        relative_entry_path = get_repository_relative_path(repo_root, entry)
        if is_ignored_repository_path(relative_entry_path, ignored_path_patterns):
            continue

        collected_entries.append(_build_tree_entry(repo_root=repo_root, target_path=entry, base_path=base_path))

        if entry.is_dir():
            collected_entries.extend(
                _collect_tree_entries(
                    repo_root=repo_root,
                    current_path=entry,
                    base_path=base_path,
                    ignored_path_patterns=ignored_path_patterns,
                )
            )

    return collected_entries


def list_repository_tree(repo_path: str, relative_repo_path: str | None = None) -> list[dict]:
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

    return _collect_tree_entries(
        repo_root=repo_root,
        current_path=target_path,
        base_path=target_path,
        ignored_path_patterns=ignored_path_patterns,
    )
