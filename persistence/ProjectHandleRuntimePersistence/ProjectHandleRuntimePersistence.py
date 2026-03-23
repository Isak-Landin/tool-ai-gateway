


class ProjectHandleRuntimePersistence:
    def __init__(self, db_connection=None):
        self.db_connection = db_connection

    def get_project_handle_runtime_fields(self, project_id: int) -> dict | None:
        """
        Expected usage:
        - called by ProjectHandle only
        - return the fields needed to construct a usable project runtime object
        - may later replace or extend the current handle-specific persistence helper
        """
        pass