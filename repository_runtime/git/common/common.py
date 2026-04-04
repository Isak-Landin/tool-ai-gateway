"""
Internal shared git execution helpers.

Ownership:
- Owns shell-backed git command assembly plus the shared strict and probe
  execution primitives used by the git command surfaces.
- Does not own action-oriented error translation or verification-facing result
  interpretation.
"""

import shlex

from errors import GitHubError
from repository_runtime.shell import ProjectShellError


def _quote_args(args) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)


def require_shell(shell_executor):
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
    shell = require_shell(shell_executor)
    shell.ensure_working_directory()

    if require_key:
        required_key_path = _require_key_path(key_path)
        shell.ensure_ssh_key_loaded(required_key_path)

    git_command = _quote_args(["git", *args])
    code, output = shell.run(git_command)
    return int(code), output.strip()


def _run_git_command_probe(
    shell_executor,
    args,
    require_key: bool = False,
    key_path: str | None = None,
) -> tuple[int, str]:
    if shell_executor is None:
        return 1, "shell_executor is required"

    try:
        shell_executor.ensure_working_directory()

        if require_key:
            normalized_key_path = str(key_path).strip()
            if not normalized_key_path:
                return 1, "key_path is required for remote git operations"
            shell_executor.ensure_ssh_key_loaded(normalized_key_path)

        git_command = _quote_args(["git", *args])
        code, output = shell_executor.run(git_command)
        return int(code), output.strip()
    except ProjectShellError as e:
        return 1, str(e)
