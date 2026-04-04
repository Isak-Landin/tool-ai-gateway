"""
Probe git command surface.

Ownership:
- Owns the low probe helper `run_git_probe(...)` plus verification/probe-oriented
  git helpers intended for runtime checks.
- Probe command helpers in this file return `bool` success/failure for expected
  git command outcomes, while `run_git_probe(...)` keeps the lower `(code, output)`
  contract for output-oriented probing.
- Delegates raw git command execution to the shared git common helpers.
"""

from repository_runtime.git.common import _run_git_command_probe


def run_git_probe(
    shell_executor,
    args,
    require_key: bool = False,
    key_path: str | None = None,
) -> tuple[int, str]:
    return _run_git_command_probe(
        shell_executor=shell_executor,
        args=args,
        require_key=require_key,
        key_path=key_path,
    )


def git_pull_probe(shell_executor, branch_name: str, key_path: str | None = None) -> bool:
    command_code, _command_output = run_git_probe(
        shell_executor=shell_executor,
        args=["pull", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )
    if command_code != 0:
        return False

    return True


def git_switch_branch_probe(
    shell_executor,
    branch_name: str,
    key_path: str | None = None,
    pull_from_origin: bool = False,
) -> bool:
    normalized_branch_name = str(branch_name).strip()
    if not normalized_branch_name:
        return False

    switch_code, _switch_output = run_git_probe(
        shell_executor=shell_executor,
        args=["checkout", normalized_branch_name],
    )
    if switch_code != 0:
        switch_code, _switch_output = run_git_probe(
            shell_executor=shell_executor,
            args=["checkout", "-b", normalized_branch_name, f"origin/{normalized_branch_name}"],
            require_key=True,
            key_path=key_path,
        )
        if switch_code != 0:
            return False

    if pull_from_origin:
        pull_ok = git_pull_probe(
            shell_executor=shell_executor,
            branch_name=normalized_branch_name,
            key_path=key_path,
        )
        if not pull_ok:
            return False

    return True


def git_push_probe(shell_executor, branch_name: str, key_path: str | None = None) -> bool:
    command_code, _command_output = run_git_probe(
        shell_executor=shell_executor,
        args=["push", "origin", branch_name],
        require_key=True,
        key_path=key_path,
    )
    if command_code != 0:
        return False

    return True


def git_add_probe(shell_executor, files=".") -> bool:
    normalized_files = files
    if isinstance(normalized_files, str):
        normalized_files = [normalized_files]
    elif not normalized_files:
        normalized_files = ["."]

    command_code, _command_output = run_git_probe(
        shell_executor=shell_executor,
        args=["add", *normalized_files],
    )
    if command_code != 0:
        return False

    return True


def git_commit_probe(shell_executor, message="+") -> bool:
    command_code, _command_output = run_git_probe(
        shell_executor=shell_executor,
        args=["commit", "-m", message],
    )
    if command_code != 0:
        return False

    return True


def clone_repo_probe(
    shell_executor,
    remote_repo_url: str,
    target_path: str,
    key_path: str | None = None,
) -> bool:
    command_code, _command_output = run_git_probe(
        shell_executor=shell_executor,
        args=["clone", remote_repo_url, target_path],
        require_key=True,
        key_path=key_path,
    )
    if command_code != 0:
        return False

    return True
