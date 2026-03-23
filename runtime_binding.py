from project_handle import ProjectHandle
from git.utils import GitHub
from persistence import ExecutionPersistence


class ProjectBindingError(Exception):
    pass


class ProjectBinder:

    def bind(self, project_row: dict) -> ProjectHandle:
        if not project_row:
            raise ProjectBindingError("project_row is required")

        handle = ProjectHandle(project_row)

        project_id = project_row.get("project_id")

        handle.bind_execution_persistence(ExecutionPersistence(project_id=project_id))

        # bind git executor
        handle.bind_git(
            GitHub(
                remote_repo_url=project_row.get("remote_repo_url"),
                local_key_path=project_row.get("key_path") or project_row.get("ssh_key"),
                local_repo_path=project_row.get("repo_path"),
                branch=project_row.get("branch") or "main",
            )
        )

        return handle
