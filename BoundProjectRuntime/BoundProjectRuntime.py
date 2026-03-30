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
        self.key_path = project_row.get("key_path") or project_row.get("ssh_key")

        self._repository_runtime = None
        self._file_runtime = None
        self._message_runtime = None

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

    def bind_file_runtime(self, file_runtime):
        """Attach the live file runtime to this bound runtime.

        Args:
            file_runtime: Project-bound file-serving dependency to store.

        Returns:
            None: The dependency is stored on the bound runtime.
        """
        self._file_runtime = file_runtime

    def bind_message_runtime(self, message_runtime):
        """Attach the live message runtime to this bound runtime.

        Args:
            message_runtime: Project-bound message-serving dependency to store.

        Returns:
            None: The dependency is stored on the bound runtime.
        """
        self._message_runtime = message_runtime

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

    @property
    def file_runtime(self):
        """Reject direct file runtime access from callers.

        Args:
            None.

        Returns:
            Never: This property always raises to enforce explicit accessor usage.
        """
        raise BoundProjectRuntimeError(
            "Direct BoundProjectRuntime.file_runtime access is deprecated; use require_file_runtime()"
        )

    @property
    def message_runtime(self):
        """Reject direct message runtime access from callers.

        Args:
            None.

        Returns:
            Never: This property always raises to enforce explicit accessor usage.
        """
        raise BoundProjectRuntimeError(
            "Direct BoundProjectRuntime.message_runtime access is deprecated; use require_message_runtime()"
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

    def require_file_runtime(self):
        """Return the bound file runtime or fail if it is missing.

        Args:
            None.

        Returns:
            Any: Bound file runtime used for live project file/tree access.
        """
        if self._file_runtime is None:
            raise BoundProjectRuntimeError("BoundProjectRuntime.file_runtime is required")

        return self._file_runtime

    def require_message_runtime(self):
        """Return the bound message runtime or fail if it is missing.

        Args:
            None.

        Returns:
            Any: Bound message runtime used for history and artifact work.
        """
        if self._message_runtime is None:
            raise BoundProjectRuntimeError("BoundProjectRuntime.message_runtime is required")

        return self._message_runtime

    def is_repository_runtime_bound(self) -> bool:
        """Report whether the repository runtime has been attached.

        Args:
            None.

        Returns:
            bool: `True` when a repository runtime is present, otherwise `False`.
        """
        return self._repository_runtime is not None

    def is_file_runtime_bound(self) -> bool:
        """Report whether the file runtime has been attached.

        Args:
            None.

        Returns:
            bool: `True` when a file runtime is present, otherwise `False`.
        """
        return self._file_runtime is not None

    def is_message_runtime_bound(self) -> bool:
        """Report whether the message runtime has been attached.

        Args:
            None.

        Returns:
            bool: `True` when a message runtime is present, otherwise `False`.
        """
        return self._message_runtime is not None

    def close(self):
        """Close bound runtime resources that expose cleanup hooks.

        Args:
            None.

        Returns:
            None: Bound runtime resources are closed in place when available.
        """
        if self._file_runtime and hasattr(self._file_runtime, "close"):
            self._file_runtime.close()
        if self._repository_runtime and hasattr(self._repository_runtime, "close"):
            self._repository_runtime.close()
