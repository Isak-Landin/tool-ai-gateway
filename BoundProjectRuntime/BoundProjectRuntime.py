"""
Bound project runtime object.

Holds one resolved `projects` row and bound project-scoped dependencies.
This class is intentionally lightweight and non-automatic. It does not resolve
DB rows, build services, or execute workflow logic by itself.
"""
from errors import BoundProjectRuntimeError


class BoundProjectRuntime:
    """Hold one project row plus its bound runtime dependencies.

    This object is intentionally passive. It stores bound dependencies and
    exposes explicit accessors instead of acting as an orchestrator.
    """

    def __init__(self, project_row: dict):
        """Initialize the bound runtime from a resolved project row.

        Args:
            project_row: Resolved project data used to seed runtime identity fields.

        Returns:
            None: The runtime holder stores project metadata and empty dependency slots.
        """
        self.project_row = project_row
        self.project_id = project_row.get("project_id")

        self.name = project_row.get("name")
        self.repo_path = project_row.get("repo_path")
        self.remote_repo_url = project_row.get("remote_repo_url")
        self.branch = project_row.get("branch") or "main"
        self.branches = list(project_row.get("branches") or [])
        self.key_path = project_row.get("key_path") or project_row.get("ssh_key")

        self._repository_runtime = None
        # Reserved for future project-scoped context management.
        self.model_context = None

    def bind_repository_runtime(self, repository_runtime):
        """Attach the repository transport runtime to this bound runtime.

        Args:
            repository_runtime: Project-bound repository transport dependency to store.

        Returns:
            None: The dependency is stored on the bound runtime.
        """
        self._repository_runtime = repository_runtime

    def bind_model_context(self, model_context_builder):
        """Attach future model-context state to the bound runtime.

        Args:
            model_context_builder: Project-scoped model context object or builder.

        Returns:
            None: The value is stored for future runtime use.
        """
        self.model_context = model_context_builder

    @property
    def repository_runtime(self):
        """Reject direct repository runtime access from callers.

        Args:
            None.

        Returns:
            Never: This property always raises to enforce explicit accessor usage.
        """
        raise BoundProjectRuntimeError(
            "Direct BoundProjectRuntime.repository_runtime access is deprecated; use require_repository_runtime()"
        )

    def require_repository_runtime(self):
        """Return the bound repository runtime or fail if it is missing.

        Args:
            None.

        Returns:
            Any: Bound repository transport runtime needed by internal callers.
        """
        if self._repository_runtime is None:
            raise BoundProjectRuntimeError("BoundProjectRuntime.repository_runtime is required")

        return self._repository_runtime

    def is_repository_runtime_bound(self) -> bool:
        """Report whether the repository runtime has been attached.

        Args:
            None.

        Returns:
            bool: `True` when a repository runtime is present, otherwise `False`.
        """
        return self._repository_runtime is not None

    def close(self):
        """Close bound runtime resources that expose cleanup hooks.

        Args:
            None.

        Returns:
            None: Bound runtime resources are closed in place when available.
        """
        if self._repository_runtime and hasattr(self._repository_runtime, "close"):
            self._repository_runtime.close()
