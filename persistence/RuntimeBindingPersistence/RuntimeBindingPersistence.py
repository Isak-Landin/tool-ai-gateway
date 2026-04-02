"""
Internal rules for runtime-binding persistence.

Ownership:
- This object owns the persistence-facing reads and builders required during
  runtime binding.
- This object does not own runtime construction, execution behavior, or message
  history composition.

Rule-set split:
- Internal method rules apply to delegation into narrower persistence owners and
  project-scope validation for repository builders.
- Encapsulated/public method rules apply to the exposed runtime-binding
  persistence methods.

Internal method rules:
- Runtime-binding field reads should delegate to
  `BoundProjectRuntimePersistence` instead of duplicating project-row loading
  logic here.
- Repository builders must require an explicit effective project id before
  returning a project-scoped persistence dependency.
- This file should build only persistence-shaped dependencies needed during
  runtime binding.

Encapsulated/public method rules:
- `get_runtime_binding_fields(...)` is the runtime-field read surface for binder
  use.
- `build_file_persistence_repository(...)` is the repository-builder surface for
  binder-owned file dependency creation.
"""

from errors import RuntimeBindingPersistenceError
from persistence.BoundProjectRuntimePersistence.BoundProjectRuntimePersistence import (
    BoundProjectRuntimePersistence,
)
from persistence.FilesRepository.FilesRepository import FilesRepository
from errors import BoundProjectRuntimePersistenceError


class RuntimeBindingPersistence:
    """
    Runtime-binding-owned persistence surface.

    This surface exists so runtime binding can:
    - load the project-scoped runtime fields needed to construct a bound runtime
      - provide the project-bound persistence-shaped dependencies needed during
        runtime construction without turning runtime binding into an execution seam
    """

    def __init__(self, db_connection=None, project_id: int | None = None):
        """Create the runtime-binding persistence surface.

        Args:
            db_connection: Optional SQLAlchemy session/connection supplied by a caller.
            project_id: Optional default project id used by repository builders.

        Returns:
            None: The helper stores persistence dependencies for later binding work.
        """
        self.db_connection = db_connection
        self.project_id = project_id
        self.bound_project_runtime_persistence = BoundProjectRuntimePersistence(db_connection=db_connection)

    def get_runtime_binding_fields(self, project_id: int) -> dict | None:
        """Load the project fields required to bind a runtime.

        Args:
            project_id: Persisted project identifier to load binding fields for.

        Returns:
            dict | None: Runtime-binding project data, or `None` when no project exists.
        """
        try:
            return self.bound_project_runtime_persistence.get_bound_project_runtime_fields(project_id)
        except BoundProjectRuntimePersistenceError as e:
            raise RuntimeBindingPersistenceError(
                str(e),
                field="project_id",
                error_type="project runtime load failed",
                file_id=__file__,
            ) from e

    def build_file_persistence_repository(
        self,
        project_id: int | None = None,
    ) -> FilesRepository:
        """Build the storage-shaped file repository for one project.

        Args:
            project_id: Optional explicit project id overriding the stored default.

        Returns:
            FilesRepository: File-row persistence helper scoped to the chosen project.
        """
        effective_project_id = project_id if project_id is not None else self.project_id

        if effective_project_id is None:
            raise RuntimeBindingPersistenceError(
                "project_id is required to build file persistence repository",
                field="project_id",
                error_type="missing project id",
                file_id=__file__,
            )

        return FilesRepository(
            db_connection=self.db_connection,
            project_id=effective_project_id,
        )
