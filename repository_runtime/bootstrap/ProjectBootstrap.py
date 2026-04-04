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
  3. `_quote_args(...)`                         - ONLY REQUIRED if we are expecting internal new function to directly replace _run_command()
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
from enum import IntEnum
from pathlib import Path

from errors import ProjectBootstrapError
from repository_runtime.shell import ProjectShell
from typing import Union


def _quote_args(command_args: list[str]) -> str:
    return " ".join(shlex.quote(str(command_arg)) for command_arg in command_args)


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
    command_args: list[str],
    *,
    failure_message: str = "",
    field: str = "",
    error_type: str = "",
) -> str:
    """
    :param shell:
    :param command_args:
    :param failure_message:
    :param field:
    :param error_type:
    :return:
    """

    required_shell = _require_shell(shell)
    required_shell.ensure_working_directory()
    command_text = _quote_args(command_args)
    command_return_code, command_output = required_shell.run(command_text)
    if command_return_code != 0:
        raise ProjectBootstrapError(
            command_output.strip() or failure_message,
            field=field,
            error_type=error_type,
            file_id=__file__,
        )

    return command_output.strip()


def _run_command_return_code(
    shell: ProjectShell | None,
    command_args: list[str],
) -> Union[str, int]:
    """
    :param shell:
    :param command_args:
    :param failure_message:
    :param field:
    :param error_type:
    :return:
    """
    # Check for missing error fields when return_code is False
    required_shell = _require_shell(shell)
    required_shell.ensure_working_directory()
    command_text = _quote_args(command_args)
    command_return_code, _command_output = required_shell.run(command_text)
    return int(command_return_code)


class Bs1VerificationFailure(IntEnum):
    PROJECTS_BASE_DIRECTORY_DIR = 1
    PROJECT_DIRECTORY_DIR = 2
    PROJECT_REPO_DIRECTORY_DIR = 3
    PROJECT_SSH_DIRECTORY_DIR = 4
    PRIVATE_KEY_FILE = 5
    PUBLIC_KEY_FILE = 6
    PROJECTS_BASE_DIRECTORY_ACCESS = 7
    SSH_KEYGEN_AVAILABLE = 8
    PRIVATE_KEY_VALID = 9
    PUBLIC_KEY_VALID = 10
    PRIVATE_KEY_READABLE = 11
    PUBLIC_KEY_READABLE = 12
    PUBLIC_KEY_NON_EMPTY = 13



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
    command_ssh_keygen_path_lookup_args = ["command", "-v", "ssh-keygen"]
    ssh_keygen_command_path = _run_command(
        shell,
        command_ssh_keygen_path_lookup_args,
        failure_message="ssh-keygen is required for project bootstrap",
        field="ssh_key",
        error_type="missing dependency",
    )

    # Keep str() convertion around ssh_keygen_path, removing it causes warning in PyCharm
    # for it being str or int when is expected, even when code_return=False is specified
    command_generate_project_keypair_args = [
        str(ssh_keygen_command_path),
        "-q",
        "-t",
        "ed25519",
        "-N",
        "",
        "-f",
        str(private_key_path),
        "-C",
        f"tool-ai-gateway-project-{project_id}",
    ]
    _run_command(
        shell,
        command_generate_project_keypair_args,
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
        public_key_text = public_key_path.read_text(encoding="utf-8").strip()
    except OSError as e:
        raise ProjectBootstrapError(
            f"Failed to read generated public key: {e}",
            field="public_key_path",
            error_type="key read failed",
            file_id=__file__,
        ) from e

    if not public_key_text:
        raise ProjectBootstrapError(
            "Generated public key is empty",
            field="public_key_path",
            error_type="key generation failed",
            file_id=__file__,
        )

    return public_key_text


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

    """
    What we should do in bs2:
    Connect repo access using existing pub key
    Materialize the repo into project repo directory, no clone in it, unpack in it.
    Materialize branch replication locally. fetch remote refs
    """

def _verify_bs1(
        *,
        project_paths: dict[str, Path],
        project_id: int,
        shell: ProjectShell | None,
) -> tuple[bool, Bs1VerificationFailure | None]:
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
      4. `shell.run(...)`
      5. translate failures to `ProjectBootstrapError`
    - Filesystem helpers should create and verify only the stage-owned paths required
      by the current bootstrap work.
    - Cleanup helpers should remove only the stage-owned filesystem state that the
      current stage created.
    - Internal helpers must stay reusable across bootstrap stage entrypoints and must
      not derive caller-owned values such as resolved project paths or shell
      instances.

      ssh_keygen -l -E SHA256 -f ./path/to/key
    :return:
    """

    required_shell = _require_shell(shell)
    required_shell.ensure_working_directory()
    projects_base_directory = project_paths["projects_base_directory"]
    project_directory = project_paths["project_directory"]
    project_repo_directory = project_paths["project_repo_directory"]
    project_ssh_directory = project_paths["project_ssh_directory"]
    private_key_path = project_paths["private_key_path"]
    public_key_path = project_paths["public_key_path"]

    # Run true path to ssh-keygen command, used in execution.
    # DO NOT RUN _quote_args() before pass for _run_command* calls!

    # --------- VERIFY ALL EXPECTED PATHS EXIST ---------- #
    for path, expected_path_type, failure_enum in (
            (projects_base_directory, "dir", Bs1VerificationFailure.PROJECTS_BASE_DIRECTORY_DIR),
            (project_directory, "dir", Bs1VerificationFailure.PROJECT_DIRECTORY_DIR),
            (project_repo_directory, "dir", Bs1VerificationFailure.PROJECT_REPO_DIRECTORY_DIR),
            (project_ssh_directory, "dir", Bs1VerificationFailure.PROJECT_SSH_DIRECTORY_DIR),
            (private_key_path, "file", Bs1VerificationFailure.PRIVATE_KEY_FILE),
            (public_key_path, "file", Bs1VerificationFailure.PUBLIC_KEY_FILE),
    ):
        if expected_path_type == "dir":
            command_verify_path_type_args = ["test", "-d", str(path)]
        else:
            command_verify_path_type_args = ["test", "-f", str(path)]

        command_return_code = _run_command_return_code(
            shell=required_shell,
            command_args=command_verify_path_type_args,
        )
        if command_return_code != 0:
            return False, failure_enum

    if not os.access(projects_base_directory, os.W_OK | os.X_OK):
        return False, Bs1VerificationFailure.PROJECTS_BASE_DIRECTORY_ACCESS

    # ------------  VERIFY KEY FILES CONTAIN KEY OF TYPE! ----------- #
    command_ssh_keygen_path_lookup_args = ["command", "-v", "ssh-keygen"]
    command_return_code = _run_command_return_code(
        shell=required_shell,
        command_args=command_ssh_keygen_path_lookup_args,
    )
    if command_return_code != 0:
        return False, Bs1VerificationFailure.SSH_KEYGEN_AVAILABLE

    key_encryption_type = "SHA256"
    command_validate_private_key_args = [
        "ssh-keygen",
        "-l",
        "-E",
        key_encryption_type,
        "-f",
        str(private_key_path),
    ]
    private_key_validation_return_code = _run_command_return_code(
        shell=required_shell,
        command_args=command_validate_private_key_args,
    )
    if private_key_validation_return_code != 0:
        return False, Bs1VerificationFailure.PRIVATE_KEY_VALID

    command_validate_public_key_args = [
        "ssh-keygen",
        "-l",
        "-E",
        key_encryption_type,
        "-f",
        str(public_key_path),
    ]
    public_key_validation_return_code = _run_command_return_code(
        shell=required_shell,
        command_args=command_validate_public_key_args,
    )
    if public_key_validation_return_code != 0:
        return False, Bs1VerificationFailure.PUBLIC_KEY_VALID

    try:
        private_key_path.read_text(encoding="utf-8")
    except OSError as e:
        return False, Bs1VerificationFailure.PRIVATE_KEY_READABLE

    try:
        public_key_path.read_text(encoding="utf-8")
    except OSError as e:
        return False, Bs1VerificationFailure.PUBLIC_KEY_READABLE

    public_key_text = public_key_path.read_text(encoding="utf-8").strip()
    if not public_key_text:
        return False, Bs1VerificationFailure.PUBLIC_KEY_NON_EMPTY

    return True, None

def _verify_bs2(
        *,
        project_paths: dict[str, Path],
        project_id: int,
        shell: ProjectShell | None,
) -> tuple[bool, None]:
    """

    :return:
    """
    return True, None

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
        verify_bs_1_ok, verify_bs_1_failure = _verify_bs1(
            project_paths=project_paths,
            project_id=project_id,
            shell=shell,
        )
        if not verify_bs_1_ok:
            return False, verify_bs_1_failure

        verify_bs_2_ok, verify_bs_2_failure = _verify_bs2(
            project_paths=project_paths,
            project_id=project_id,
            shell=shell,
        )
        if not verify_bs_2_ok:
            return False, verify_bs_2_failure

        return True, None
    except ProjectBootstrapError:
        raise
