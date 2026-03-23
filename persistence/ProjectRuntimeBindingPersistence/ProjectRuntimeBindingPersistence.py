


class ProjectRuntimeBindingPersistence:
    def __init__(self, db_connection=None):
        self.db_connection = db_connection

    def get_project_runtime_binding_fields(self, project_id: int) -> dict | None:
        """
        Expected usage:
        - called by runtime binding only
        - return the fields needed to bind runtime services and accessors
        - keep runtime-binding needs separate from route-facing project reads
        """
        pass