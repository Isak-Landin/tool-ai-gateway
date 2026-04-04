"""
Internal shared git execution helpers.

Ownership:
- Owns shell-backed git command assembly and the lowest non-raising git execution
  contract used by both strict and probe git surfaces.
- Does not own action-oriented error translation or verification-facing result
  interpretation.
"""

import shlex

from errors import GitHubError


def _quote_args(args) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)


def _require_shell(shell_executor):
    if shell_executor is None:
        raise GitHubError(message="shell_executor is required")

    return shell_executor


def _require_key_path(key_path: str | None) -> str:
    normalized_key_path = str(key_path).strip()
    if not normalized_key_path:
        raise GitHubError(message="key_path is required for remote git operations")

    return normalized_key_path


def _run_git_command(
    shell_executor,
    args,
    require_key: bool = False,
    key_path: str | None = None,
) -> tuple[int, str]:
    shell = _require_shell(shell_executor)
    shell.ensure_working_directory()

    if require_key:
        required_key_path = _require_key_path(key_path)
        shell.ensure_ssh_key_loaded(required_key_path)

    git_command = _quote_args(["git", *args])
    code, output = shell.run(git_command)
    return int(code), output.strip()


def _run_clone_repo(
    shell_executor,
    remote_repo_url: str,
    target_path: str,
    key_path: str | None = None,
) -> tuple[int, str]:
    shell = _require_shell(shell_executor)
    shell.ensure_working_directory()
    required_key_path = _require_key_path(key_path)
    shell.ensure_ssh_key_loaded(required_key_path)

    clone_command = _quote_args(["git", "clone", remote_repo_url, target_path])
    code, output = shell.run(clone_command)
    return int(code), output.strip()
