"""
Probe git command surface.

Ownership:
- Owns verification/probe-oriented git helpers intended for runtime checks where
  normal git failure should remain available as `(code, output)` data.
- Delegates raw git command execution to the shared git common helpers.
"""

from errors import GitHubError
from repository_runtime.git.common import _run_clone_repo, _run_git_command


def run_git_probe(
    shell_executor,
    args,
    require_key: bool = False,
    key_path: str | None = None,
) -> tuple[int, str]:
    try:
        return _run_git_command(
            shell_executor=shell_executor,
            args=args,
            require_key=require_key,
            key_path=key_path,
        )
    except GitHubError:
        raise
    except Exception as e:
        raise GitHubError(message=str(e))


def git_pull_probe(shell_executor, branch_name: str, key_path: str | None = None) -> tuple[int, str]:
    return run_git_probe(
        shell_executor=shell_executor,
        args=["pull", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )


def git_switch_branch_probe(
    shell_executor,
    branch_name: str,
    key_path: str | None = None,
    pull_from_origin: bool = False,
):
    normalized_branch_name = str(branch_name).strip()
    if not normalized_branch_name:
        raise GitHubError(message="branch_name is required")

    switch_code, switch_output = run_git_probe(
        shell_executor=shell_executor,
        args=["checkout", normalized_branch_name],
    )
    if switch_code != 0:
        switch_code, switch_output = run_git_probe(
            shell_executor=shell_executor,
            args=["checkout", "-b", normalized_branch_name, f"origin/{normalized_branch_name}"],
            require_key=True,
            key_path=key_path,
        )

    result = {
        "branch_name": normalized_branch_name,
        "switch_code": switch_code,
        "switch_output": switch_output,
    }

    if pull_from_origin:
        pull_code, pull_output = git_pull_probe(
            shell_executor=shell_executor,
            branch_name=normalized_branch_name,
            key_path=key_path,
        )
        result["pull_code"] = pull_code
        result["pull_output"] = pull_output

    return result


def git_push_probe(shell_executor, branch_name: str, key_path: str | None = None) -> tuple[int, str]:
    return run_git_probe(
        shell_executor=shell_executor,
        args=["push", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )


def git_add_probe(shell_executor, files=".") -> tuple[int, str]:
    normalized_files = files
    if isinstance(normalized_files, str):
        normalized_files = [normalized_files]
    elif not normalized_files:
        normalized_files = ["."]

    return run_git_probe(
        shell_executor=shell_executor,
        args=["add", *normalized_files],
    )


def git_commit_probe(shell_executor, message="+") -> tuple[int, str]:
    return run_git_probe(
        shell_executor=shell_executor,
        args=["commit", "-m", message],
    )


def clone_repo_probe(
    shell_executor,
    remote_repo_url: str,
    target_path: str,
    key_path: str | None = None,
) -> tuple[int, str]:
    try:
        return _run_clone_repo(
            shell_executor=shell_executor,
            remote_repo_url=remote_repo_url,
            target_path=target_path,
            key_path=key_path,
        )
    except GitHubError:
        raise
    except Exception as e:
        raise GitHubError(message=str(e))
