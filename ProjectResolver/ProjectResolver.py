from typing import Any

from errors import ResolutionPersistenceError
from persistence import ResolutionPersistence


class ProjectResolutionError(Exception):
    """Raised when project resolution cannot complete successfully."""

    pass


class ProjectNotFoundError(ProjectResolutionError):
    """Raised when a requested project id does not exist."""

    pass


class ProjectResolver:
    """Resolve persisted project identity data for higher backend layers.

    The resolver stays narrow: it confirms the project and returns the fields
    needed to hand resolution upward.
    """

    def __init__(self, db_connection: Any = None, requesting_route=None):
        """Create a project resolver with optional shared dependencies.

        Args:
            db_connection: Optional SQLAlchemy session/connection supplied by a caller.
            requesting_route: Optional route metadata retained for future diagnostics.

        Returns:
            None: The resolver stores the persistence dependency for later use.
        """
        self.db_connection = db_connection
        self.resolution_persistence = ResolutionPersistence(db_connection)
        self.requesting_route = requesting_route

    def resolve_by_id(self, project_id: int) -> dict:
        """Resolve one persisted project row by project id.

        Args:
            project_id: Persisted project identifier to resolve.

        Returns:
            dict: Resolution-shaped project data for runtime binding.
        """
        if project_id is None:
            raise ProjectResolutionError("project_id is required")

        try:
            project_row = self.resolution_persistence.get_project_resolution_fields(project_id)
        except ResolutionPersistenceError as e:
            raise ProjectResolutionError(str(e)) from e

        if not project_row:
            raise ProjectNotFoundError(f"Project not found for id={project_id}")

        return project_row
