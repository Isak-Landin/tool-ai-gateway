from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import shlex


IGNORED_PATHS_CONFIG_PATH = Path(__file__).resolve().parent / "ignored_paths.json"


def get_repository_ignore_patterns() -> list[str]:
    config_data = json.loads(IGNORED_PATHS_CONFIG_PATH.read_text(encoding="utf-8"))
    configured_patterns = config_data.get("ignored_path_patterns")
    if not isinstance(configured_patterns, list):
        raise ValueError("ignored_path_patterns must be a list")

    ignore_patterns: list[str] = []
    for configured_pattern in configured_patterns:
        normalized_pattern = str(configured_pattern).strip()
        if normalized_pattern:
            ignore_patterns.append(normalized_pattern)

    return ignore_patterns


def normalize_repository_relative_path(
    relative_repo_path: str | None = None,
    *,
    allow_root: bool = True,
) -> str:
    normalized_relative_path = str(relative_repo_path or "").strip()
    if normalized_relative_path in {"", ".", "/"}:
        if allow_root:
            return "/"
        raise ValueError("relative_repo_path must not point to the repository root")

    normalized_relative_path = normalized_relative_path.lstrip("/")
    normalized_parts: list[str] = []
    for path_part in PurePosixPath(normalized_relative_path).parts:
        if path_part in {"", "."}:
            continue
        if path_part == "..":
            raise ValueError(f"Path escapes repository root: {relative_repo_path}")
        normalized_parts.append(path_part)

    if not normalized_parts:
        if allow_root:
            return "/"
        raise ValueError("relative_repo_path must not point to the repository root")

    return "/" + "/".join(normalized_parts)


def resolve_repository_target(repo_path: str, relative_repo_path: str | None = None) -> tuple[Path, Path]:
    if not str(repo_path).strip():
        raise ValueError("repo_path is required")

    repo_root = Path(repo_path).expanduser().resolve()
    if not repo_root.exists():
        raise ValueError(f"Repository path does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise ValueError(f"Repository path is not a directory: {repo_root}")

    normalized_relative_path = normalize_repository_relative_path(relative_repo_path, allow_root=True)
    if normalized_relative_path == "/":
        target_path = repo_root
    else:
        target_path = (repo_root / normalized_relative_path.lstrip("/")).resolve()

    try:
        target_path.relative_to(repo_root)
    except ValueError as e:
        raise ValueError(f"Path escapes repository root: {relative_repo_path}") from e

    if not target_path.exists():
        scoped_path = relative_repo_path or "/"
        raise ValueError(f"Path does not exist in repository: {scoped_path}")

    return repo_root, target_path


def get_repository_relative_path(repo_root: Path, target_path: Path) -> str:
    relative_path = target_path.relative_to(repo_root)
    if str(relative_path) == ".":
        return "/"

    return "/" + relative_path.as_posix()


def is_ignored_repository_path(relative_repo_path: str, ignore_patterns: list[str]) -> bool:
    normalized_relative_path = relative_repo_path.lstrip("/")
    if normalized_relative_path in {"", "."}:
        return False

    relative_path = PurePosixPath(normalized_relative_path)
    return any(relative_path.match(ignore_pattern) for ignore_pattern in ignore_patterns)


def build_ripgrep_ignore_args(ignore_patterns: list[str]) -> list[str]:
    rg_args: list[str] = []
    for ignore_pattern in ignore_patterns:
        rg_args.extend(["-g", f"!{ignore_pattern}"])

    return rg_args


def get_repository_shell_target_argument(repo_root: Path, target_path: Path) -> str:
    if target_path == repo_root:
        return "."

    relative_target_path = target_path.relative_to(repo_root).as_posix()
    return "./" + relative_target_path


def quote_shell_args(args: list[str]) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)
