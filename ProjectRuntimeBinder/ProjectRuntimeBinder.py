from BoundProjectRuntime import BoundProjectRuntime
from persistence import RuntimeBindingPersistence
from repository_runtime.shell import ProjectShell


class ProjectRuntimeBindingError(Exception):
    pass


class ProjectRuntimeBinder:
    def _require_project_id(self, project_row: dict) -> int:
        project_id = project_row.get("project_id")
        if project_id is None:
            raise ProjectRuntimeBindingError("project_id is required for runtime binding")

        return project_id

    def _require_repo_path(self, project_row: dict) -> str:
        repo_path = project_row.get("repo_path")
        if not str(repo_path).strip():
            raise ProjectRuntimeBindingError("repo_path is required for runtime binding")

        return str(repo_path).strip()

    def _resolve_effective_branch(self, project_row: dict, branch_override: str | None = None) -> str:
        if branch_override is not None and str(branch_override).strip():
            return str(branch_override).strip()

        return str(project_row.get("branch") or "main").strip()

    def _require_bound_runtime_preconditions(self, bound_project_runtime: BoundProjectRuntime) -> None:
        if bound_project_runtime.project_id is None:
            raise ProjectRuntimeBindingError("BoundProjectRuntime.project_id is required")

        if not str(bound_project_runtime.repo_path).strip():
            raise ProjectRuntimeBindingError("BoundProjectRuntime.repo_path is required")

        if not bound_project_runtime.is_execution_persistence_bound():
            raise ProjectRuntimeBindingError("BoundProjectRuntime.execution_persistence must be bound")

        if not bound_project_runtime.is_shell_bound():
            raise ProjectRuntimeBindingError("BoundProjectRuntime.shell must be bound")

    def bind(self, project_row: dict, branch_override: str | None = None) -> BoundProjectRuntime:
        if not project_row:
            raise ProjectRuntimeBindingError("project_row is required")

        project_id = self._require_project_id(project_row)
        repo_path = self._require_repo_path(project_row)
        effective_branch = self._resolve_effective_branch(project_row, branch_override=branch_override)

        bound_project_runtime = BoundProjectRuntime(project_row)
        bound_project_runtime.branch = effective_branch

        bound_project_runtime.bind_shell(
            ProjectShell(
                working_directory=repo_path,
            )
        )

        bound_project_runtime.bind_execution_persistence(
            RuntimeBindingPersistence(
                project_id=project_id,
                repo_path=repo_path,
            )
        )

        self._require_bound_runtime_preconditions(bound_project_runtime)

        return bound_project_runtime
