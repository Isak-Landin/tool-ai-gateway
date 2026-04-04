"""
Strict git command surface.

Ownership:
- Owns action-oriented git helpers intended for normal runtime work where
  non-zero git exit codes should raise `GitHubError`.
- Delegates raw git command execution to the shared git common helpers.
"""

from errors import GitHubError
from repository_runtime.git.common import _run_clone_repo, _run_git_command


def run_git(
    shell_executor,
    args,
    require_key: bool = False,
    key_path: str | None = None,
    allowed_return_codes: set[int] | None = None,
):
    try:
        command_code, command_output = _run_git_command(
            shell_executor=shell_executor,
            args=args,
            require_key=require_key,
            key_path=key_path,
        )
        effective_allowed_return_codes = allowed_return_codes or {0}
        if command_code not in effective_allowed_return_codes:
            raise GitHubError(message=command_output or f"Git command failed with code {command_code}")

        return command_output
    except GitHubError:
        raise
    except Exception as e:
        raise GitHubError(message=str(e))


def git_pull(shell_executor, branch_name: str, key_path: str | None = None):
    return run_git(
        shell_executor=shell_executor,
        args=["pull", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )


def git_switch_branch(
    shell_executor,
    branch_name: str,
    key_path: str | None = None,
    pull_from_origin: bool = False,
):
    normalized_branch_name = str(branch_name).strip()
    if not normalized_branch_name:
        raise GitHubError(message="branch_name is required")

    try:
        switch_output = run_git(
            shell_executor=shell_executor,
            args=["checkout", normalized_branch_name],
        )
    except GitHubError:
        switch_output = run_git(
            shell_executor=shell_executor,
            args=["checkout", "-b", normalized_branch_name, f"origin/{normalized_branch_name}"],
            require_key=True,
            key_path=key_path,
        )

    result = {
        "branch_name": normalized_branch_name,
        "switch_output": switch_output,
    }

    if pull_from_origin:
        result["pull_output"] = git_pull(
            shell_executor=shell_executor,
            branch_name=normalized_branch_name,
            key_path=key_path,
        )

    return result


def git_push(shell_executor, branch_name: str, key_path: str | None = None):
    return run_git(
        shell_executor=shell_executor,
        args=["push", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )


def git_add(shell_executor, files="."):
    normalized_files = files
    if isinstance(normalized_files, str):
        normalized_files = [normalized_files]
    elif not normalized_files:
        normalized_files = ["."]

    return run_git(
        shell_executor=shell_executor,
        args=["add", *normalized_files],
    )


def git_commit(shell_executor, message="+"):
    return run_git(
        shell_executor=shell_executor,
        args=["commit", "-m", message],
    )


def clone_repo(shell_executor, remote_repo_url: str, target_path: str, key_path: str | None = None):
    try:
        command_code, command_output = _run_clone_repo(
            shell_executor=shell_executor,
            remote_repo_url=remote_repo_url,
            target_path=target_path,
            key_path=key_path,
        )
        if command_code != 0:
            raise GitHubError(message=command_output or "Failed to clone repository")

        return command_output
    except GitHubError:
        raise
    except Exception as e:
        raise GitHubError(message=str(e))
