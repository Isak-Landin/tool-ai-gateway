from repository_runtime.git import git_switch_branch


def execute_switch_repository_branch(
    shell_executor,
    branch_name: str,
    key_path: str | None = None,
    pull_from_origin: bool = False,
) -> bool:
    return git_switch_branch(
        shell_executor=shell_executor,
        branch_name=branch_name,
        key_path=key_path,
        pull_from_origin=pull_from_origin,
    )
