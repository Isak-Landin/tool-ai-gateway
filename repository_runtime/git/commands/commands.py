"""
Strict git command surface.

Ownership:
- Owns action-oriented git helpers intended for normal runtime work.
- Action helpers in this file return `bool` success/failure for expected git
  command outcomes.
- Delegates raw git command execution to the shared git common helpers.
"""

from repository_runtime.git.common import _run_git_command


def git_pull(shell_executor, branch_name: str, key_path: str | None = None) -> bool:
    command_code, _command_output = _run_git_command(
        shell_executor=shell_executor,
        args=["pull", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )
    if command_code != 0:
        return False

    return True


def git_switch_branch(
    shell_executor,
    branch_name: str,
    key_path: str | None = None,
    pull_from_origin: bool = False,
) -> bool:
    normalized_branch_name = str(branch_name).strip()
    if not normalized_branch_name:
        return False

    switch_code, _switch_output = _run_git_command(
        shell_executor=shell_executor,
        args=["checkout", normalized_branch_name],
    )
    if switch_code != 0:
        switch_code, _switch_output = _run_git_command(
            shell_executor=shell_executor,
            args=["checkout", "-b", normalized_branch_name, f"origin/{normalized_branch_name}"],
            require_key=True,
            key_path=key_path,
        )
        if switch_code != 0:
            return False

    if pull_from_origin:
        pull_ok = git_pull(
            shell_executor=shell_executor,
            branch_name=normalized_branch_name,
            key_path=key_path,
        )
        if not pull_ok:
            return False

    return True


def git_push(shell_executor, branch_name: str, key_path: str | None = None) -> bool:
    command_code, _command_output = _run_git_command(
        shell_executor=shell_executor,
        args=["push", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )
    if command_code != 0:
        return False

    return True


def git_add(shell_executor, files=".") -> bool:
    normalized_files = files
    if isinstance(normalized_files, str):
        normalized_files = [normalized_files]
    elif not normalized_files:
        normalized_files = ["."]

    command_code, _command_output = _run_git_command(
        shell_executor=shell_executor,
        args=["add", *normalized_files],
    )
    if command_code != 0:
        return False

    return True


def git_commit(shell_executor, message="+") -> bool:
    command_code, _command_output = _run_git_command(
        shell_executor=shell_executor,
        args=["commit", "-m", message],
    )
    if command_code != 0:
        return False

    return True


def clone_repo(shell_executor, remote_repo_url: str, target_path: str, key_path: str | None = None) -> bool:
    command_code, _command_output = _run_git_command(
        shell_executor=shell_executor,
        args=["clone", remote_repo_url, target_path],
        require_key=True,
        key_path=key_path,
    )
    if command_code != 0:
        return False

    return True
