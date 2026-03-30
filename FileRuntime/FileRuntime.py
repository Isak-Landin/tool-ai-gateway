from __future__ import annotations

from errors import FileRuntimeError, RepositoryFilePersistenceError
from repository_runtime import list_repository_tree, read_repository_file, search_repository_text


class FileRuntime:
    """
    Project-bound live file/tree runtime surface.

    This object owns project-scoped live repository reads for file/tree consumers.
    It may also reuse persistence-shaped file storage when explicitly requested,
    but it does not turn file persistence into the live serving owner.
    """

    def __init__(
        self,
        *,
        project_id: int,
        repo_path: str,
        branch: str,
        repository_runtime,
        files_repository=None,
    ):
        if project_id is None:
            raise FileRuntimeError("project_id is required")
        if not str(repo_path).strip():
            raise FileRuntimeError("repo_path is required")
        if repository_runtime is None:
            raise FileRuntimeError("repository_runtime is required")

        self.project_id = project_id
        self.repo_path = str(repo_path).strip()
        self.branch = str(branch or "main").strip()
        self.repository_runtime = repository_runtime
        self.files_repository = files_repository

    def _require_files_repository(self):
        if self.files_repository is None:
            raise FileRuntimeError("files_repository is required for persistence-backed file operations")

        return self.files_repository

    def list_tree(self, relative_repo_path: str | None = None) -> list[dict]:
        try:
            return list_repository_tree(
                shell_executor=self.repository_runtime.shell,
                repo_path=self.repo_path,
                relative_repo_path=relative_repo_path,
            )
        except ValueError as e:
            raise FileRuntimeError(str(e)) from e

    def read_file(
        self,
        relative_repo_path: str,
        start_line: int | None = None,
        number_of_lines: int | None = None,
        end_line: int | None = None,
    ) -> dict:
        try:
            return read_repository_file(
                repo_path=self.repo_path,
                relative_repo_path=relative_repo_path,
                start_line=start_line,
                number_of_lines=number_of_lines,
                end_line=end_line,
            )
        except ValueError as e:
            raise FileRuntimeError(str(e)) from e

    def search_text(
        self,
        query: str,
        relative_repo_path: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> list[dict]:
        try:
            return search_repository_text(
                shell_executor=self.repository_runtime.shell,
                repo_path=self.repo_path,
                query=query,
                relative_repo_path=relative_repo_path,
                case_sensitive=case_sensitive,
                max_results=max_results,
            )
        except ValueError as e:
            raise FileRuntimeError(str(e)) from e

    def list_persisted_files(self) -> list[dict]:
        files_repository = self._require_files_repository()
        try:
            return files_repository.list_by_project()
        except RepositoryFilePersistenceError as e:
            raise FileRuntimeError(str(e)) from e

    def get_persisted_file(self, relative_repo_path: str) -> dict | None:
        files_repository = self._require_files_repository()
        try:
            return files_repository.get_by_path(relative_repo_path)
        except RepositoryFilePersistenceError as e:
            raise FileRuntimeError(str(e)) from e

    def persist_file_snapshot(self, relative_repo_path: str) -> dict:
        live_file = self.read_file(relative_repo_path=relative_repo_path)
        files_repository = self._require_files_repository()
        try:
            return files_repository.upsert_file(
                relative_repo_path=live_file["path"],
                name=live_file["name"],
                content=live_file["content"],
                total_lines=live_file["total_lines"],
            )
        except RepositoryFilePersistenceError as e:
            raise FileRuntimeError(str(e)) from e
