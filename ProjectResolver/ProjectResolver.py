from typing import Any

from errors import ResolutionPersistenceError
from persistence import ResolutionPersistence


class ProjectResolutionError(Exception):
    pass


class ProjectNotFoundError(ProjectResolutionError):
    pass


class ProjectResolver:
    def __init__(self, db_connection: Any = None, requesting_route=None):
        self.db_connection = db_connection
        self.resolution_persistence = ResolutionPersistence(db_connection)
        self.requesting_route = requesting_route

    def resolve_by_id(self, project_id: int) -> dict:
        if project_id is None:
            raise ProjectResolutionError("project_id is required")

        try:
            project_row = self.resolution_persistence.get_project_resolution_fields(project_id)
        except ResolutionPersistenceError as e:
            raise ProjectResolutionError(str(e)) from e

        if not project_row:
            raise ProjectNotFoundError(f"Project not found for id={project_id}")

        return project_row
