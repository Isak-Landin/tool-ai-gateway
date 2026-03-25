import shlex

from errors import GitHubError


def _quote_args(args) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)


def _require_shell(shell_executor):
    if shell_executor is None:
        raise GitHubError(message="shell_executor is required")

    return shell_executor


def _require_key_path(key_path: str | None) -> str:
    if not str(key_path).strip():
        raise GitHubError(message="key_path is required for remote git operations")

    return str(key_path).strip()


def run_git(shell_executor, args, require_key: bool = False, key_path: str | None = None):
    try:
        shell = _require_shell(shell_executor)

        if require_key:
            shell.ensure_ssh_key_loaded(_require_key_path(key_path))

        git_command = _quote_args(["git", *args])
        code, output = shell.run(git_command)
        if code != 0:
            raise GitHubError(message=output.strip() or f"Git command failed with code {code}")

        return output.strip()
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
        shell = _require_shell(shell_executor)
        shell.ensure_ssh_key_loaded(_require_key_path(key_path))

        clone_command = _quote_args(["git", "clone", remote_repo_url, target_path])
        code, output = shell.run(clone_command)
        if code != 0:
            raise GitHubError(message=output.strip() or "Failed to clone repository")

        return output.strip()
    except GitHubError:
        raise
    except Exception as e:
        raise GitHubError(message=str(e))
