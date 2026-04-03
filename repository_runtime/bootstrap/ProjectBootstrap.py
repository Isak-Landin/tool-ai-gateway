"""
Internal rules for bootstrap stage helpers.

Ownership:
- This file owns reusable bootstrap-stage helpers that operate on caller-resolved
  paths and caller-owned shell dependencies.
- This file owns stage-local filesystem preparation, stage-local shell-backed
  work, and stage-local cleanup for bootstrap failures.
- This file does not own project-row persistence, project-path derivation, shell
  creation, or route/UI progression decisions.

Rule-set split:
- Internal helper rules apply to shared bootstrap primitives such as command
  execution, stage-local storage preparation, stage-local key generation, and
  stage-local cleanup.
- Encapsulated/public helper rules apply to bootstrap stage entrypoints such as
  `bs1(...)` and other stage entrypoints defined in this
  file.

Internal helper rules:
- Shell-backed helpers must use this order:
  1. `_require_shell(...)`
  2. `shell.ensure_working_directory()`
  3. `_quote_args(...)`
  4. `shell.run(...)`
  5. translate failures to `ProjectBootstrapError`
- Filesystem helpers should create and verify only the stage-owned paths required
  by the current bootstrap work.
- Cleanup helpers should remove only the stage-owned filesystem state that the
  current stage created.
- Internal helpers must stay reusable across bootstrap stage entrypoints and must
  not derive caller-owned values such as resolved project paths or shell
  instances.

Encapsulated/public helper rules:
- Each bootstrap stage entrypoint should compose only the internal helpers
  required for that stage's use case.
- Each bootstrap stage entrypoint should accept caller-owned dependencies and
  resolved values explicitly rather than deriving them internally.
- Each bootstrap stage entrypoint owns stage-level cleanup and error propagation
  for the internal helpers it composes.
- Entry points for remote-repository interaction stages should compose the
  corresponding shell/key-preparation internal helpers instead of introducing a
  different execution order.
"""

import os
import shlex
import shutil
from pathlib import Path

from errors import ProjectBootstrapError
from repository_runtime.shell import ProjectShell


def _quote_args(args: list[str]) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)


def _require_shell(shell: ProjectShell | None) -> ProjectShell:
    if shell is None:
        raise ProjectBootstrapError(
            "shell is required for shell-backed bootstrap work",
            field="shell",
            error_type="missing dependency",
            file_id=__file__,
        )

    return shell


def _run_command(
    shell: ProjectShell | None,
    args: list[str],
    *,
    failure_message: str,
    field: str,
    error_type: str,
) -> str:
    required_shell = _require_shell(shell)
    required_shell.ensure_working_directory()
    command = _quote_args(args)
    code, output = required_shell.run(command)
    if code != 0:
        raise ProjectBootstrapError(
            output.strip() or failure_message,
            field=field,
            error_type=error_type,
            file_id=__file__,
        )

    return output.strip()


def _create_project_storage(project_paths: dict[str, Path]) -> None:
    projects_base_directory = project_paths["projects_base_directory"]
    project_directory = project_paths["project_directory"]
    project_repo_directory = project_paths["project_repo_directory"]
    project_ssh_directory = project_paths["project_ssh_directory"]

    try:
        projects_base_directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ProjectBootstrapError(
            f"Failed to create PROJECTS_ROOT directory: {e}",
            field="PROJECTS_ROOT",
            error_type="directory create failed",
            file_id=__file__,
        ) from e

    if not projects_base_directory.is_dir():
        raise ProjectBootstrapError(
            f"PROJECTS_ROOT is not a directory: {projects_base_directory}",
            field="PROJECTS_ROOT",
            error_type="invalid configuration",
            file_id=__file__,
        )

    if not os.access(projects_base_directory, os.W_OK | os.X_OK):
        raise ProjectBootstrapError(
            f"PROJECTS_ROOT is not writable: {projects_base_directory}",
            field="PROJECTS_ROOT",
            error_type="permission denied",
            file_id=__file__,
        )

    if project_directory.exists():
        raise ProjectBootstrapError(
            f"Project directory already exists: {project_directory}",
            field="repo_path",
            error_type="path conflict",
            file_id=__file__,
        )

    try:
        project_directory.mkdir(parents=True, exist_ok=False)
        project_repo_directory.mkdir(parents=False, exist_ok=False)
        project_ssh_directory.mkdir(parents=False, exist_ok=False)
    except OSError as e:
        raise ProjectBootstrapError(
            f"Failed to create project storage directories: {e}",
            field="repo_path",
            error_type="directory create failed",
            file_id=__file__,
        ) from e

    if not project_repo_directory.is_dir():
        raise ProjectBootstrapError(
            f"Project repo directory was not created: {project_repo_directory}",
            field="repo_path",
            error_type="directory create failed",
            file_id=__file__,
        )

    if not project_ssh_directory.is_dir():
        raise ProjectBootstrapError(
            f"Project SSH directory was not created: {project_ssh_directory}",
            field="ssh_key",
            error_type="directory create failed",
            file_id=__file__,
        )


def _generate_project_keypair(
    *,
    shell: ProjectShell | None,
    private_key_path: Path,
    public_key_path: Path,
    project_id: int,
) -> str:
    ssh_keygen_path = _run_command(
        shell,
        ["command", "-v", "ssh-keygen"],
        failure_message="ssh-keygen is required for project bootstrap",
        field="ssh_key",
        error_type="missing dependency",
    )

    _run_command(
        shell,
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


def _cleanup_project_storage(project_directory: Path | None) -> None:
    if project_directory is None or not project_directory.exists():
        return

    shutil.rmtree(project_directory, ignore_errors=True)


def bs1(
    *,
    project_paths: dict[str, Path],
    project_id: int,
    shell: ProjectShell | None,
) -> bool:
    try:
        _create_project_storage(project_paths)
        _generate_project_keypair(
            shell=shell,
            private_key_path=project_paths["private_key_path"],
            public_key_path=project_paths["public_key_path"],
            project_id=project_id,
        )
        return True
    except ProjectBootstrapError:
        _cleanup_project_storage(project_paths.get("project_directory"))
        raise


# Remaining BS2, we need verification of expected things having been created.
# These include verification of existing storage
"""
Internal helper rules:
- Shell-backed helpers must use this order:
  1. `_require_shell(...)`
  2. `shell.ensure_working_directory()`
  3. `_quote_args(...)`
  4. `shell.run(...)`
  5. translate failures to `ProjectBootstrapError`
"""
def bs2 (
        *,
        project_paths: dict[str, Path],
        project_id: int,
        shell: ProjectShell | None,
):
    # Verify existence of disk project, keys, db row
    # verify existence of remote repo
    # Verify possibility to read/write to remove - only read has to be available, aka pull
    """
    project_id
    repo_path
    remote_repo_url
    branches
    ssh_key
    public_key_path
    created_at
    updated_at

    messages: Mapped[list["Message"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Message.sequence_no",
    )
    :return:
    """

def _verify_bs1(
        *,
        project_paths: dict[str, Path],
        project_id: int,
        shell: ProjectShell | None,
) -> bool:
    """
    EXPECTED in project_paths:
    projects_base_directory
    project_directory
    project_repo_directory
    project_ssh_directory
    private_key_path
    public_key_path

    return {
    "projects_base_directory": projects_base_directory,
    "project_directory": project_directory,
    "project_repo_directory": project_directory / "repo",
    "project_ssh_directory": project_ssh_directory,
    "private_key_path": project_ssh_directory / "id_ed25519",
    "public_key_path": project_ssh_directory / "id_ed25519.pub",
    }

    Internal helper rules:
    - Shell-backed helpers must use this order:
      1. `_require_shell(...)`
      2. `shell.ensure_working_directory()`
      3. `_quote_args(...)`
      4. `shell.run(...)`
      5. translate failures to `ProjectBootstrapError`
    - Filesystem helpers should create and verify only the stage-owned paths required
      by the current bootstrap work.
    - Cleanup helpers should remove only the stage-owned filesystem state that the
      current stage created.
    - Internal helpers must stay reusable across bootstrap stage entrypoints and must
      not derive caller-owned values such as resolved project paths or shell
      instances.

      ssh-keygen -l -f ~/.ssh/id_ed25519 1> /dev/null
    :return:
    """

    required_shell = _require_shell(shell)
    required_shell.ensure_working_directory()
    projects_base_directory = project_paths["base_directory"]
    project_directory = project_paths["project_directory"]
    project_repo_directory = project_paths["repo_directory"]
    project_ssh_directory = project_paths["ssh_directory"]
    private_key_path = project_paths["private_key_path"]
    public_key_path = project_paths["public_key_path"]

def _verify_bs2(
        *,
        project_paths: dict[str, Path],
        project_id: int,
        shell: ProjectShell | None,
) -> bool:
    """

    :return:
    """

def verify_bs_all(
        *,
        project_paths: dict[str, Path],
        project_id: int,
        shell: ProjectShell | None,
):
    """
    RUNS ON LOAD PROJECT PAGE. VERIFY BOTH BS1 AND BS2
    :return:
    """
    try:
        verify_bs_1 = _verify_bs1(
            project_paths=project_paths,
            project_id=project_id,
            shell=shell,
        )

        verify_bs_2 = _verify_bs2(
            project_paths=project_paths,
            project_id=project_id,
            shell=shell,
        )

        return verify_bs_1 and verify_bs_2
    except ProjectBootstrapError:
        raise

