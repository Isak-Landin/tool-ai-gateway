"""
Internal rules for resolution persistence.

Ownership:
- This object owns the minimal persisted project fields required by project
  resolution.
- This object does not own runtime binding, bootstrap, or broader project-row
  persistence behavior.

Rule-set split:
- Internal method rules apply to narrow resolution-field loading.
- Encapsulated/public method rules apply to the exposed resolution read.

Internal method rules:
- Reads in this file should stay limited to the minimal fields required for
  project resolution.
- This file should not evolve into a general project repository or attach other
  persistence/runtime dependencies.

Encapsulated/public method rules:
- `get_project_resolution_fields(...)` is the resolution read surface and should
  remain a narrow resolver dependency only.
"""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.models import Project
from db.session import SessionLocal
from errors import ResolutionPersistenceError


class ResolutionPersistence:
    """Persistence surface for narrow project resolution reads."""

    def __init__(self, db_connection=None):
        """Create the resolution persistence helper.

        Args:
            db_connection: Optional SQLAlchemy session/connection supplied by a caller.

        Returns:
            None: The helper stores the DB dependency for later reads.
        """
        self.db_connection = db_connection

    def get_project_resolution_fields(self, project_id: int) -> dict | None:
        """Load the minimal project fields needed by project resolution.

        Args:
            project_id: Persisted project identifier to resolve.

        Returns:
            dict | None: Resolution-shaped project data, or `None` when no project exists.
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
            }
        except SQLAlchemyError as e:
            raise ResolutionPersistenceError(
                str(e),
                field="project_id",
                error_type="sql error",
                file_id=__file__,
            ) from e
        finally:
            if self.db_connection is None:
                session.close()
