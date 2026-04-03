from BoundProjectRuntime import BoundProjectRuntime
from errors import BoundProjectRuntimeError, RuntimeBindingPersistenceError
from persistence import RuntimeBindingPersistence
from repository_runtime import RepositoryRuntime


class ProjectRuntimeBindingError(Exception):
    """Raised when runtime binding cannot produce a usable bound runtime."""

    pass


class ProjectRuntimeBinder:
    """Turn a resolved project row into a usable bound runtime.

    The binder owns dependency attachment only. It does not resolve projects or
    execute workflow logic.
    """

    def __init__(self, db_connection=None, runtime_binding_persistence: RuntimeBindingPersistence | None = None):
        """Create a runtime binder with optional shared persistence dependencies.

        Args:
            db_connection: Optional SQLAlchemy session/connection supplied by a caller.
            runtime_binding_persistence: Optional specialized persistence surface for binding work.

        Returns:
            None: The binder stores the persistence dependency for later binding.
        """
        self.db_connection = db_connection
        self.runtime_binding_persistence = runtime_binding_persistence or RuntimeBindingPersistence(
            db_connection=db_connection
        )

    def _require_project_id(self, resolved_project: dict) -> int:
        """Extract the resolved project id or fail when it is missing.

        Args:
            resolved_project: Resolution-shaped project data from the resolver.

        Returns:
            int: Persisted project identifier needed for runtime binding.
        """
        project_id = resolved_project.get("project_id")
        if project_id is None:
            raise ProjectRuntimeBindingError("project_id is required for runtime binding")

        return project_id

    def _require_repo_path(self, project_row: dict) -> str:
        """Extract the repository path required for runtime binding.

        Args:
            project_row: Runtime-binding project data loaded from persistence.

        Returns:
            str: Normalized repository path for the bound runtime.
        """
        repo_path = project_row.get("repo_path")
        if not str(repo_path).strip():
            raise ProjectRuntimeBindingError("repo_path is required for runtime binding")

        return str(repo_path).strip()

    def _resolve_effective_branch(self, project_row: dict, branch_override: str | None = None) -> str:
        """Choose the branch that the bound runtime should use.

        Args:
            project_row: Runtime-binding project data containing the stored branch.
            branch_override: Optional branch override requested by the caller.

        Returns:
            str: Effective branch value for the bound runtime.
        """
        if branch_override is not None and str(branch_override).strip():
            return str(branch_override).strip()

        return str(project_row.get("branch") or "main").strip()

    def _require_bound_runtime_preconditions(self, bound_project_runtime: BoundProjectRuntime) -> None:
        """Verify that the bound runtime contains all required dependencies.

        Args:
            bound_project_runtime: Newly built runtime to validate before returning.

        Returns:
            None: Validation succeeds silently or raises a binding error.
        """
        if bound_project_runtime.project_id is None:
            raise ProjectRuntimeBindingError("BoundProjectRuntime.project_id is required")

        if not str(bound_project_runtime.repo_path).strip():
            raise ProjectRuntimeBindingError("BoundProjectRuntime.repo_path is required")

        try:
            bound_project_runtime.require_repository_runtime()
        except BoundProjectRuntimeError as e:
            raise ProjectRuntimeBindingError(str(e)) from e

    def _load_runtime_binding_fields(self, project_id: int) -> dict:
        """Load the persistence fields required to construct a bound runtime.

        Args:
            project_id: Persisted project identifier to load binding fields for.

        Returns:
            dict: Runtime-binding project data used to attach dependencies.
        """
        try:
            project_row = self.runtime_binding_persistence.get_runtime_binding_fields(project_id)
        except RuntimeBindingPersistenceError as e:
            raise ProjectRuntimeBindingError(str(e)) from e

        if not project_row:
            raise ProjectRuntimeBindingError(f"Project runtime fields not found for id={project_id}")

        return project_row

    def bind(self, resolved_project: dict, branch_override: str | None = None) -> BoundProjectRuntime:
        """Bind project-scoped dependencies onto a new runtime holder.

        Args:
            resolved_project: Resolution-shaped project data from the resolver.
            branch_override: Optional branch value to use instead of the stored branch.

        Returns:
            BoundProjectRuntime: Fully bound runtime holder with attached dependencies.
        """
        if not resolved_project:
            raise ProjectRuntimeBindingError("resolved_project is required")

        project_id = self._require_project_id(resolved_project)
        project_row = self._load_runtime_binding_fields(project_id)
        repo_path = self._require_repo_path(project_row)
        effective_branch = self._resolve_effective_branch(project_row, branch_override=branch_override)

        bound_project_runtime = BoundProjectRuntime(project_row)
        bound_project_runtime.branch = effective_branch

        bound_project_runtime.bind_repository_runtime(
            RepositoryRuntime(
                repo_path=repo_path,
                branch=effective_branch,
                key_path=project_row.get("key_path") or project_row.get("ssh_key"),
                remote_repo_url=project_row.get("remote_repo_url"),
            )
        )

        self._require_bound_runtime_preconditions(bound_project_runtime)

        return bound_project_runtime
