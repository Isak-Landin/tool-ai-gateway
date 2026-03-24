from persistence.ExecutionPersistence.ExecutionPersistence import ExecutionPersistence


class RuntimeBindingPersistence(ExecutionPersistence):
    """
    Runtime-binding-owned persistence surface.

    This surface exists so runtime binding does not depend directly on the
    execution persistence class, while still being able to provide the
    execution-facing persistence dependency that the bound runtime exposes.
    """

    def __init__(self, db_connection=None, project_id: int | None = None, repo_path: str | None = None):
        super().__init__(
            db_connection=db_connection,
            project_id=project_id,
            repo_path=repo_path,
        )
