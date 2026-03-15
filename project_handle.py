"""
Runtime project binding object.

Holds one resolved `projects` row and bound project-scoped executors/accessors.
This class is intentionally lightweight and non-automatic. It does not resolve
DB rows, build services, or execute workflow logic by itself.
"""


class ProjectHandle:
    def __init__(self, project_row: dict):
        self.project_row = project_row
        self.project_id = project_row.get("id")

        self.repo_path = project_row.get("repo_path")
        self.remote_repo_url = project_row.get("remote_repo_url")
        self.branch = project_row.get("branch", "main")
        self.key_path = project_row.get("key_path")

        self.git = None
        self.files = None
        self.messages = None
        self.shell = None

        self.tools = None
        self.model_context = None

    def bind_git(self, git_executor):
        self.git = git_executor

    def bind_files_accessor(self, files_accessor):
        self.files = files_accessor

    def bind_messages_accessor(self, messages_accessor):
        self.messages = messages_accessor

    def bind_shell(self, shell_executor):
        self.shell = shell_executor

    def bind_tools(self, tools_executor):
        self.tools = tools_executor

    def bind_model_context(self, model_context_builder):
        self.model_context = model_context_builder

    def is_git_bound(self) -> bool:
        return self.git is not None

    def is_files_bound(self) -> bool:
        return self.files is not None

    def is_messages_bound(self) -> bool:
        return self.messages is not None

    def is_shell_bound(self) -> bool:
        return self.shell is not None

    def close(self):
        if self.shell and hasattr(self.shell, "close"):
            self.shell.close()

        if self.git and hasattr(self.git, "close"):
            self.git.close()