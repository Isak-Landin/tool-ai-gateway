"""
Bound project runtime object.

Holds one resolved `projects` row and bound project-scoped dependencies.
This class is intentionally lightweight and non-automatic. It does not resolve
DB rows, build services, or execute workflow logic by itself.
"""
class BoundProjectRuntime:
    def __init__(self, project_row: dict):
        self.project_row = project_row
        self.project_id = project_row.get("project_id")

        self.name = project_row.get("name")
        self.ai_model_name = project_row.get("ai_model_name")
        self.repo_path = project_row.get("repo_path")
        self.remote_repo_url = project_row.get("remote_repo_url")
        self.branch = project_row.get("branch") or "main"
        self.key_path = project_row.get("key_path") or project_row.get("ssh_key")

        self.execution_persistence = None
        self.repository_runtime = None

        # Reserved for future project-scoped context management.
        self.model_context = None

    def bind_execution_persistence(self, execution_persistence):
        self.execution_persistence = execution_persistence

    def bind_repository_runtime(self, repository_runtime):
        self.repository_runtime = repository_runtime

    def bind_model_context(self, model_context_builder):
        self.model_context = model_context_builder

    def is_execution_persistence_bound(self) -> bool:
        return self.execution_persistence is not None

    def is_repository_runtime_bound(self) -> bool:
        return self.repository_runtime is not None

    def close(self):
        if self.repository_runtime and hasattr(self.repository_runtime, "close"):
            self.repository_runtime.close()
