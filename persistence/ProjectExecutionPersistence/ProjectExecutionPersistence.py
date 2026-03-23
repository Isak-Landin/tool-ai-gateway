




class ProjectExecutionPersistence:
    def __init__(self, db_connection=None, project_id: int | None = None):
        self.db_connection = db_connection
        self.project_id = project_id

    def list_execution_messages(self) -> list[dict]:
        """
        Expected usage:
        - called by execution/orchestration only
        - return message history in the shape execution expects
        - support prompt reconstruction and tool replay later
        """
        pass

    def insert_execution_message(self, message_data: dict) -> dict:
        """
        Expected usage:
        - called by execution/orchestration only
        - persist user, assistant, and tool turns in execution-owned shapes
        """
        pass

    def list_selected_file_context(self, selected_files: list[str]) -> list[dict]:
        """
        Expected usage:
        - called by execution/orchestration only
        - return file context rows for selected repo-scoped files
        """
        pass
