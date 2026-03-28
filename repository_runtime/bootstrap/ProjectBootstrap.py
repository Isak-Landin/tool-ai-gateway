import os
import shlex
import shutil
from pathlib import Path

from errors import ProjectBootstrapError
from repository_runtime.shell import ProjectShell


class ProjectBootstrap:
    def __init__(self, shell: ProjectShell | None = None):
        self.shell = shell or ProjectShell()
        self._owns_shell = shell is None

    def _quote_args(self, args: list[str]) -> str:
        return " ".join(shlex.quote(str(arg)) for arg in args)

    def _run_command(self, args: list[str], failure_message: str, field: str, error_type: str) -> str:
        code, output = self.shell.run(self._quote_args(args))
        if code != 0:
            raise ProjectBootstrapError(
                output.strip() or failure_message,
                field=field,
                error_type=error_type,
                file_id=__file__,
            )

        return output.strip()

    def create_project_storage(self, project_paths: dict[str, Path]) -> None:
        projects_root = project_paths["projects_root"]
        project_root = project_paths["project_root"]
        repo_path = project_paths["repo_path"]
        ssh_directory = project_paths["ssh_directory"]

        try:
            projects_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ProjectBootstrapError(
                f"Failed to create PROJECTS_ROOT directory: {e}",
                field="PROJECTS_ROOT",
                error_type="directory create failed",
                file_id=__file__,
            ) from e

        if not projects_root.is_dir():
            raise ProjectBootstrapError(
                f"PROJECTS_ROOT is not a directory: {projects_root}",
                field="PROJECTS_ROOT",
                error_type="invalid configuration",
                file_id=__file__,
            )

        if not os.access(projects_root, os.W_OK | os.X_OK):
            raise ProjectBootstrapError(
                f"PROJECTS_ROOT is not writable: {projects_root}",
                field="PROJECTS_ROOT",
                error_type="permission denied",
                file_id=__file__,
            )

        if project_root.exists():
            raise ProjectBootstrapError(
                f"Project storage root already exists: {project_root}",
                field="repo_path",
                error_type="path conflict",
                file_id=__file__,
            )

        try:
            project_root.mkdir(parents=True, exist_ok=False)
            repo_path.mkdir(parents=False, exist_ok=False)
            ssh_directory.mkdir(parents=False, exist_ok=False)
        except OSError as e:
            raise ProjectBootstrapError(
                f"Failed to create project storage directories: {e}",
                field="repo_path",
                error_type="directory create failed",
                file_id=__file__,
            ) from e

        if not repo_path.is_dir():
            raise ProjectBootstrapError(
                f"Project repo directory was not created: {repo_path}",
                field="repo_path",
                error_type="directory create failed",
                file_id=__file__,
            )

        if not ssh_directory.is_dir():
            raise ProjectBootstrapError(
                f"Project SSH directory was not created: {ssh_directory}",
                field="ssh_key",
                error_type="directory create failed",
                file_id=__file__,
            )

    def generate_project_keypair(
        self,
        private_key_path: Path,
        public_key_path: Path,
        project_id: int,
    ) -> str:
        ssh_keygen_path = self._run_command(
            ["command", "-v", "ssh-keygen"],
            failure_message="ssh-keygen is required for project bootstrap",
            field="ssh_key",
            error_type="missing dependency",
        )

        self._run_command(
            [
                ssh_keygen_path,
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-f",
                str(private_key_path),
                "-C",
                f"tool-ai-gateway-project-{project_id}",
            ],
            failure_message="Failed to generate project SSH keypair",
            field="ssh_key",
            error_type="key generation failed",
        )

        if not private_key_path.is_file():
            raise ProjectBootstrapError(
                f"Generated private key file is missing: {private_key_path}",
                field="ssh_key",
                error_type="key generation failed",
                file_id=__file__,
            )

        if not public_key_path.is_file():
            raise ProjectBootstrapError(
                f"Generated public key file is missing: {public_key_path}",
                field="public_key_path",
                error_type="key generation failed",
                file_id=__file__,
            )

        try:
            public_key = public_key_path.read_text(encoding="utf-8").strip()
        except OSError as e:
            raise ProjectBootstrapError(
                f"Failed to read generated public key: {e}",
                field="public_key_path",
                error_type="key read failed",
                file_id=__file__,
            ) from e

        if not public_key:
            raise ProjectBootstrapError(
                "Generated public key is empty",
                field="public_key_path",
                error_type="key generation failed",
                file_id=__file__,
            )

        return public_key

    def cleanup_project_storage(self, project_root: Path | None) -> None:
        if project_root is None or not project_root.exists():
            return

        shutil.rmtree(project_root, ignore_errors=True)

    def close(self) -> None:
        if self._owns_shell and self.shell and hasattr(self.shell, "close"):
            self.shell.close()
