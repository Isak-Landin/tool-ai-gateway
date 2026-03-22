from project_handle import ProjectHandle
from git.utils import GitHub
from persistence import MessagesRepository, FilesRepository, ProjectBindingPersistence


class ProjectBindingError(Exception):
    pass


class ProjectBinder:

    def bind(self, project_row: dict) -> ProjectHandle:
        if not project_row:
            raise ProjectBindingError("project_row is required")

        handle = ProjectHandle(project_row)

        project_id = project_row.get("project_id")
        binding_data = None
        if project_id is not None:
            binding_data = ProjectBindingPersistence().get_project_binding_fields(project_id)

        binding_data = binding_data or {}

        # bind persistence accessors
        handle.bind_messages_accessor(MessagesRepository(project_id=project_id))
        handle.bind_files_accessor(
            FilesRepository(
                project_id=project_id,
                repo_path=project_row.get("repo_path") or binding_data.get("repo_path"),
            )
        )

        # bind git executor
        handle.bind_git(
            GitHub(
                remote_repo_url=project_row.get("remote_repo_url") or binding_data.get("remote_repo_url"),
                local_key_path=(
                    project_row.get("key_path")
                    or project_row.get("ssh_key")
                    or binding_data.get("ssh_key")
                ),
                local_repo_path=project_row.get("repo_path") or binding_data.get("repo_path"),
                branch=project_row.get("branch") or binding_data.get("branch") or "main",
            )
        )

        return handle
