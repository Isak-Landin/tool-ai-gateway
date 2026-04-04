"""
Internal rules for bound-runtime field persistence.

Ownership:
- This object owns the narrow persisted project fields required to construct a
  bound project runtime.
- This object does not own runtime construction, runtime dependency builders, or
  broader project persistence behavior.

Rule-set split:
- Internal method rules apply to narrow project-row loading and runtime-shaped
  field selection.
- Encapsulated/public method rules apply to the exposed bound-runtime field read.

Internal method rules:
- Reads in this file should stay limited to the fields required for bound runtime
  construction.
- This file should return runtime-construction data only and should not shape
  route responses or attach lower dependencies.

Encapsulated/public method rules:
- `get_bound_project_runtime_fields(...)` is the only bound-runtime field read
  surface in this file and should remain narrow.
"""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.models import Project
from db.session import SessionLocal
from errors import BoundProjectRuntimePersistenceError


class BoundProjectRuntimePersistence:
    """Persistence surface for loading bound-runtime construction fields."""

    def __init__(self, db_connection=None):
        """Create the bound-runtime persistence helper.

        Args:
            db_connection: Optional SQLAlchemy session/connection supplied by a caller.

        Returns:
            None: The helper stores the DB dependency for later reads.
        """
        self.db_connection = db_connection

    def get_bound_project_runtime_fields(self, project_id: int) -> dict | None:
        """Load the project fields needed to construct a bound runtime.

        Args:
            project_id: Persisted project identifier to load runtime fields for.

        Returns:
            dict | None: Runtime-binding project data, or `None` when no project exists.
        """
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project).where(Project.project_id == project_id)
            project = session.execute(stmt).scalar_one_or_none()
            if project is None:
                return None

            return {
                "project_id": project.project_id,
                "name": project.name,
                "repo_path": project.repo_path,
                "remote_repo_url": project.remote_repo_url,
                "branch": project.branch,
                "branches": list(project.branches or []),
                "ssh_key": project.ssh_key,
                "public_key_path": project.public_key_path,
            }
        except SQLAlchemyError as e:
            raise BoundProjectRuntimePersistenceError(
                str(e),
                field="project_id",
                error_type="sql error",
                file_id=__file__,
            ) from e
        finally:
            if self.db_connection is None:
                session.close()
