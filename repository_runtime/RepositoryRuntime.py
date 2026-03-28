from repository_runtime.shell import ProjectShell


class RepositoryRuntime:
    def __init__(
        self,
        repo_path: str,
        branch: str,
        key_path: str | None = None,
        remote_repo_url: str | None = None,
    ):
        self.repo_path = repo_path
        self.branch = branch
        self.key_path = key_path
        self.remote_repo_url = remote_repo_url
        self.shell = ProjectShell(working_directory=repo_path)

    def close(self):
        if self.shell and hasattr(self.shell, "close"):
            self.shell.close()
