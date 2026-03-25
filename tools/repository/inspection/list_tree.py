from repository_runtime.inspection import list_repository_tree


def execute_list_repository_tree(
    shell_executor,
    repo_path: str,
    relative_repo_path: str | None = None,
) -> list[dict]:
    return list_repository_tree(
        shell_executor=shell_executor,
        repo_path=repo_path,
        relative_repo_path=relative_repo_path,
    )
