from repository_runtime.inspection import search_repository_text


def execute_search_repository_text(
    shell_executor,
    repo_path: str,
    query: str,
    relative_repo_path: str | None = None,
    case_sensitive: bool = False,
    max_results: int = 100,
) -> list[dict]:
    return search_repository_text(
        shell_executor=shell_executor,
        repo_path=repo_path,
        query=query,
        relative_repo_path=relative_repo_path,
        case_sensitive=case_sensitive,
        max_results=max_results,
    )
