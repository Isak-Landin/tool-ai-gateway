from errors import RuntimeBindingPersistenceError
from persistence.ExecutionPersistence.ExecutionPersistence import ExecutionPersistence
from persistence.BoundProjectRuntimePersistence.BoundProjectRuntimePersistence import (
    BoundProjectRuntimePersistence,
)
from persistence.FilesRepository.FilesRepository import FilesRepository
from persistence.MessagesRepository.MessagesRepository import MessagesRepository
from errors import BoundProjectRuntimePersistenceError


class RuntimeBindingPersistence:
    """
    Runtime-binding-owned persistence surface.

    This surface exists so runtime binding can:
    - load the project-scoped runtime fields needed to construct a bound runtime
    - provide the execution-facing persistence dependency without depending on
      execution's class shape as its own base type
    """

    def __init__(self, db_connection=None, project_id: int | None = None, repo_path: str | None = None):
        self.db_connection = db_connection
        self.project_id = project_id
        self.repo_path = repo_path
        self.bound_project_runtime_persistence = BoundProjectRuntimePersistence(db_connection=db_connection)

    def get_runtime_binding_fields(self, project_id: int) -> dict | None:
        try:
            return self.bound_project_runtime_persistence.get_bound_project_runtime_fields(project_id)
        except BoundProjectRuntimePersistenceError as e:
            raise RuntimeBindingPersistenceError(
                str(e),
                field="project_id",
                error_type="project runtime load failed",
                file_id=__file__,
            ) from e

    def build_execution_persistence(
        self,
        project_id: int | None = None,
        repo_path: str | None = None,
    ) -> ExecutionPersistence:
        effective_project_id = project_id if project_id is not None else self.project_id
        effective_repo_path = repo_path if repo_path is not None else self.repo_path

        if effective_project_id is None:
            raise RuntimeBindingPersistenceError(
                "project_id is required to build execution persistence",
                field="project_id",
                error_type="missing project id",
                file_id=__file__,
            )

        if not str(effective_repo_path).strip():
            raise RuntimeBindingPersistenceError(
                "repo_path is required to build execution persistence",
                field="repo_path",
                error_type="missing repo path",
                file_id=__file__,
            )

        return ExecutionPersistence(
            db_connection=self.db_connection,
            project_id=effective_project_id,
            repo_path=str(effective_repo_path).strip(),
        )

    def build_files_repository(
        self,
        project_id: int | None = None,
        repo_path: str | None = None,
    ) -> FilesRepository:
        effective_project_id = project_id if project_id is not None else self.project_id
        effective_repo_path = repo_path if repo_path is not None else self.repo_path

        if effective_project_id is None:
            raise RuntimeBindingPersistenceError(
                "project_id is required to build files repository",
                field="project_id",
                error_type="missing project id",
                file_id=__file__,
            )

        return FilesRepository(
            db_connection=self.db_connection,
            project_id=effective_project_id,
            repo_path=(
                str(effective_repo_path).strip()
                if effective_repo_path is not None and str(effective_repo_path).strip()
                else None
            ),
        )

    def build_messages_repository(
        self,
        project_id: int | None = None,
    ) -> MessagesRepository:
        effective_project_id = project_id if project_id is not None else self.project_id

        if effective_project_id is None:
            raise RuntimeBindingPersistenceError(
                "project_id is required to build messages repository",
                field="project_id",
                error_type="missing project id",
                file_id=__file__,
            )

        return MessagesRepository(
            db_connection=self.db_connection,
            project_id=effective_project_id,
        )
