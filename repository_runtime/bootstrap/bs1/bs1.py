"""
BS1 setup and verification.
"""

import os
import shutil
from enum import IntEnum
from pathlib import Path

from errors import ProjectBootstrapError
from repository_runtime.bootstrap.common import _require_shell, _run_command, _run_command_return_output
from repository_runtime.shell import ProjectShell


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
) -> str:
    command_ssh_keygen_path_lookup_args = ["command", "-v", "ssh-keygen"]
    ssh_keygen_command_path = _run_command_return_output(
        shell,
        command_ssh_keygen_path_lookup_args,
        failure_message="ssh-keygen is required for project bootstrap",
        field="ssh_key",
        error_type="missing dependency",
    )

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
        "Tool-AI-Gateway",
    ]
    _run_command_return_output(
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
    shell: ProjectShell | None,
) -> bool:
    try:
        _create_project_storage(project_paths)
        _generate_project_keypair(
            shell=shell,
            private_key_path=project_paths["private_key_path"],
            public_key_path=project_paths["public_key_path"],
        )
        return True
    except ProjectBootstrapError:
        _cleanup_project_storage(project_paths.get("project_directory"))
        raise


def _verify_bs1(
    *,
    project_paths: dict[str, Path],
    shell: ProjectShell | None,
) -> tuple[bool, Bs1VerificationFailure | None]:
    required_shell = _require_shell(shell)
    required_shell.ensure_working_directory()
    projects_base_directory = project_paths["projects_base_directory"]
    project_directory = project_paths["project_directory"]
    project_repo_directory = project_paths["project_repo_directory"]
    project_ssh_directory = project_paths["project_ssh_directory"]
    private_key_path = project_paths["private_key_path"]
    public_key_path = project_paths["public_key_path"]

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

        command_return_code, _command_output = _run_command(
            shell=required_shell,
            command_args=command_verify_path_type_args,
        )
        if command_return_code != 0:
            return False, failure_enum

    if not os.access(projects_base_directory, os.W_OK | os.X_OK):
        return False, Bs1VerificationFailure.PROJECTS_BASE_DIRECTORY_ACCESS

    command_ssh_keygen_path_lookup_args = ["command", "-v", "ssh-keygen"]
    command_return_code, _command_output = _run_command(
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
    private_key_validation_return_code, _command_output = _run_command(
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
    public_key_validation_return_code, _command_output = _run_command(
        shell=required_shell,
        command_args=command_validate_public_key_args,
    )
    if public_key_validation_return_code != 0:
        return False, Bs1VerificationFailure.PUBLIC_KEY_VALID

    try:
        private_key_path.read_text(encoding="utf-8")
    except OSError:
        return False, Bs1VerificationFailure.PRIVATE_KEY_READABLE

    try:
        public_key_path.read_text(encoding="utf-8")
    except OSError:
        return False, Bs1VerificationFailure.PUBLIC_KEY_READABLE

    public_key_text = public_key_path.read_text(encoding="utf-8").strip()
    if not public_key_text:
        return False, Bs1VerificationFailure.PUBLIC_KEY_NON_EMPTY

    return True, None
