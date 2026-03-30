from errors import FileRuntimeError
from repository_runtime.shell import ProjectShell


class RepositoryRuntime:
    """
    Project-bound repository transport surface.

    This object owns the bound shell and git transport context. It is not the
    live file/tree/search owner for shared consumers.
    """
    def __init__(
        self,
        repo_path: str,
        branch: str,
        key_path: str | None = None,
        remote_repo_url: str | None = None,
    ):
        """Create the project-bound repository transport runtime.

        Args:
            repo_path: Local repository path that the bound shell should use.
            branch: Effective branch value associated with this runtime.
            key_path: Optional SSH private-key path for git transport work.
            remote_repo_url: Optional remote repository URL for git transport work.

        Returns:
            None: The runtime stores transport metadata and opens a bound shell.
        """
        self.repo_path = repo_path
        self.branch = branch
        self.key_path = key_path
        self.remote_repo_url = remote_repo_url
        self.shell = ProjectShell(working_directory=repo_path)

    def close(self):
        """Close the bound project shell if it is still available.

        Args:
            None.

        Returns:
            None: Shell resources are released in place.
        """
        if self.shell and hasattr(self.shell, "close"):
            self.shell.close()

    def _raise_live_file_runtime_deprecation(self, method_name: str) -> None:
        """Fail when callers try to use repository transport as a live file owner.

        Args:
            method_name: Deprecated method name the caller attempted to use.

        Returns:
            Never: This helper always raises a file-runtime error.
        """
        raise FileRuntimeError(
            f"RepositoryRuntime.{method_name} is deprecated for live file/tree access; use the bound FileRuntime surface"
        )

    def load_selected_context(self, selected_files: list[str]) -> list[dict]:
        """Reject deprecated live selected-context access on repository transport.

        Args:
            selected_files: Repo-relative file paths requested by the caller.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("load_selected_context")

    def list_tree(self, relative_repo_path: str | None = None) -> list[dict]:
        """Reject deprecated live tree access on repository transport.

        Args:
            relative_repo_path: Optional repo-relative directory path the caller requested.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("list_tree")

    def read_file(
        self,
        relative_repo_path: str,
        start_line: int | None = None,
        number_of_lines: int | None = None,
        end_line: int | None = None,
    ) -> dict:
        """Reject deprecated live file access on repository transport.

        Args:
            relative_repo_path: Repo-relative file path the caller requested.
            start_line: Optional first line number to include.
            number_of_lines: Optional count of lines to include from `start_line`.
            end_line: Optional inclusive last line number to include.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("read_file")

    def search_text(
        self,
        query: str,
        relative_repo_path: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> list[dict]:
        """Reject deprecated live text-search access on repository transport.

        Args:
            query: Search query the caller attempted to run.
            relative_repo_path: Optional repo-relative path to limit the search scope.
            case_sensitive: Whether the attempted search preserved letter case.
            max_results: Maximum number of matches the caller requested.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("search_text")
