from BoundProjectRuntime import BoundProjectRuntime
from FileRuntime import FileRuntime
from MessageRuntime import MessageRuntime
from errors import RuntimeBindingPersistenceError
from persistence import RuntimeBindingPersistence
from repository_runtime import RepositoryRuntime


class ProjectRuntimeBindingError(Exception):
    pass


class ProjectRuntimeBinder:
    def __init__(self, db_connection=None, runtime_binding_persistence: RuntimeBindingPersistence | None = None):
        self.db_connection = db_connection
        self.runtime_binding_persistence = runtime_binding_persistence or RuntimeBindingPersistence(
            db_connection=db_connection
        )

    def _require_project_id(self, resolved_project: dict) -> int:
        project_id = resolved_project.get("project_id")
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

        if not bound_project_runtime.is_repository_runtime_bound():
            raise ProjectRuntimeBindingError("BoundProjectRuntime.repository_runtime must be bound")

        if not bound_project_runtime.is_file_runtime_bound():
            raise ProjectRuntimeBindingError("BoundProjectRuntime.file_runtime must be bound")

        if not bound_project_runtime.is_message_runtime_bound():
            raise ProjectRuntimeBindingError("BoundProjectRuntime.message_runtime must be bound")

    def _load_runtime_binding_fields(self, project_id: int) -> dict:
        try:
            project_row = self.runtime_binding_persistence.get_runtime_binding_fields(project_id)
        except RuntimeBindingPersistenceError as e:
            raise ProjectRuntimeBindingError(str(e)) from e

        if not project_row:
            raise ProjectRuntimeBindingError(f"Project runtime fields not found for id={project_id}")

        return project_row

    def bind(self, resolved_project: dict, branch_override: str | None = None) -> BoundProjectRuntime:
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

        bound_project_runtime.bind_execution_persistence(
            self.runtime_binding_persistence.build_execution_persistence(
                project_id=project_id,
                repo_path=repo_path,
            )
        )

        bound_project_runtime.bind_file_runtime(
            FileRuntime(
                project_id=project_id,
                repo_path=repo_path,
                branch=effective_branch,
                repository_runtime=bound_project_runtime.repository_runtime,
                files_repository=self.runtime_binding_persistence.build_files_repository(
                    project_id=project_id,
                    repo_path=repo_path,
                ),
            )
        )

        bound_project_runtime.bind_message_runtime(
            MessageRuntime(
                project_id=project_id,
                messages_repository=self.runtime_binding_persistence.build_messages_repository(
                    project_id=project_id,
                ),
            )
        )

        self._require_bound_runtime_preconditions(bound_project_runtime)

        return bound_project_runtime
