"""
BS2 setup and verification.

BS2 is the second bootstrap setup stage. It owns making a BS1-complete project
usable as a real local repository. It does not own persistence writes, route/UI
flow decisions, or later branch-discovery/storage responsibilities.
"""

import shlex
from pathlib import Path
from enum import IntEnum

from repository_runtime.bootstrap.common import run_command
from repository_runtime.shell import ProjectShell
from errors import ProjectBootstrapError

class Bs2VerificationFailure(IntEnum):
    BS1_VERIFICATION = 1

class Bs2VerificationFailureRepresentation(IntEnum):
    PROJECT_REPO_DIRECTORY_NOT_GIT_REPOSITORY = 1
    ORIGIN_REMOTE_URL_MISMATCH = 2
    ORIGIN_REMOTE_UNREACHABLE = 3


def bs2(
        *,
        project_paths: dict[str, Path],
        shell: ProjectShell | None,
        remote_repo_url: str,
) -> bool:

    """
    Owns:
    1. using the existing SSH key to establish repository access
    2. materializing the repository into project_repo_directory

    Must not own:
    1. project-row writes
    2. commit / rollback behavior
    3. route or UI redirect decisions
    4. verification reporting
    5. repair policy
    6. deriving/storing the real branch list as persisted project data
    7. deriving/storing the effective default branch as persisted project data
    
    
    project_paths:
        projects_base_directory
        project_directory
        project_repo_directory
        project_ssh_directory
        private_key_path
        public_key_path
    """
    _project_paths = project_paths
    _project_paths_str = {k: str(v) for k, v in project_paths.items()}

    project_repo_directory = _project_paths_str["project_repo_directory"]
    private_key_path = _project_paths_str["private_key_path"]
    remote_repo_url = remote_repo_url

    from repository_runtime.bootstrap.bs1 import _verify_bs1 as verify_bs1
    # Should likely ensure with verification of bs1, even though this creates duplicate behavior.
    # Even though it has "possibly" - almost certainly - occurred in the exact same called origin just before bs2 execution
    is_bs1_verified, _ = verify_bs1(project_paths=project_paths, shell=shell)
    if not is_bs1_verified:
        raise ProjectBootstrapError(
            message="During bs2 runtime, bs1 verification failed",
            field=__file__,
            error_type="VerificationFailure",
        )

    from repository_runtime.git import clone_repo
    is_cloned_repo = clone_repo(
        shell_executor=shell,
        remote_repo_url=remote_repo_url,
        target_path=project_repo_directory,
        key_path=private_key_path,
    )
    if not is_cloned_repo:
        raise ProjectBootstrapError(
            message="Could not clone project from remote repo",
            field=__file__,
            error_type="CloneFailure",
        )

    return True



def _verify_bs2(
    *,
    project_paths: dict[str, Path],
    shell: ProjectShell | None,
    remote_repo_url: str,
) -> tuple[bool, Bs2VerificationFailureRepresentation | None]:
    """
    **Owns**

    - checking resulting BS2 state after BS2 should have completed
    - checking only these three BS2 verification concerns:
      1. `git -C "<project_repo_directory>" rev-parse --is-inside-work-tree`
      2. `git -C "<project_repo_directory>" remote get-url origin` against expected `remote_repo_url`
      3. `GIT_SSH_COMMAND='ssh -i "<private_key_path>" -o IdentitiesOnly=yes' git -C "<project_repo_directory>" ls-remote --heads origin`
    - returning the first BS2 verification failure identifier
    - staying limited to verification/reporting of resulting BS2 state

    **Must not own**

    - BS2 setup itself
    - project-row writes
    - repair execution
    - route or UI output shaping
    - later branch-discovery/storage responsibilities
    """
    project_repo_directory = str(project_paths["project_repo_directory"])
    private_key_path = str(project_paths["private_key_path"])
    normalized_remote_repo_url = str(remote_repo_url).strip()

    command_return_code, command_output = run_command(
        shell=shell,
        command_args=["git", "-C", project_repo_directory, "rev-parse", "--is-inside-work-tree"],
    )
    if command_return_code != 0 or command_output != "true":
        return False, Bs2VerificationFailureRepresentation.PROJECT_REPO_DIRECTORY_NOT_GIT_REPOSITORY

    command_return_code, command_output = run_command(
        shell=shell,
        command_args=["git", "-C", project_repo_directory, "remote", "get-url", "origin"],
    )
    if command_return_code != 0 or command_output != normalized_remote_repo_url:
        return False, Bs2VerificationFailureRepresentation.ORIGIN_REMOTE_URL_MISMATCH

    git_ssh_command = f"ssh -i {shlex.quote(private_key_path)} -o IdentitiesOnly=yes"
    command_return_code, _command_output = run_command(
        shell=shell,
        command_args=[
            "env",
            f"GIT_SSH_COMMAND={git_ssh_command}",
            "git",
            "-C",
            project_repo_directory,
            "ls-remote",
            "--heads",
            "origin",
        ],
    )
    if command_return_code != 0:
        return False, Bs2VerificationFailureRepresentation.ORIGIN_REMOTE_UNREACHABLE

    return True, None
