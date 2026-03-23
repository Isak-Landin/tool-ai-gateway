from errors import ResolutionPersistenceError


class ProjectResolutionPersistence:
    def __init__(self, db_connection=None):
        self.db_connection = db_connection

    def get_project_resolution_fields(self, project_id: int) -> dict | None:
        """
        Expected usage:
        - called by project resolution only
        - resolve a project-scoped row by project_id
        - return the fields project resolution intends to hand upward
        """
        pass
