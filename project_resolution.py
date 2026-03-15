from typing import Any

from persistence import ProjectsRepository


class ProjectResolutionError(Exception):
    pass


class ProjectNotFoundError(ProjectResolutionError):
    pass


class ProjectResolver:
    def __init__(self, db_connection: Any = None):
        self.db_connection = db_connection
        self.projects_repo = ProjectsRepository(db_connection)

    def resolve_by_id(self, project_id: int) -> dict:
        if project_id is None:
            raise ProjectResolutionError("project_id is required")

        project_row = self.projects_repo.get_project_by_id(project_id)

        if not project_row:
            raise ProjectNotFoundError(f"Project not found for id={project_id}")

        return project_row