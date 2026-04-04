"""
BS2 setup and verification.
"""

from pathlib import Path

from repository_runtime.shell import ProjectShell


def bs2(
    *,
    project_paths: dict[str, Path],
    shell: ProjectShell | None,
):
    # Verify existence of disk project, keys, db row
    # verify existence of remote repo
    # Verify possibility to read/write to remove - only read has to be available, aka pull
    """
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
        order_by="Message.sequence_no"
    )
    :return:
    """

    """
    Owns:
    1. using the existing SSH key to establish repository access
    2. materializing the repository into project_repo_directory
    3. fetching remote refs
    4. materializing real branch state locally
    5. deriving resulting branch reality from the actual local repository after setup
    6. deriving the active/default branch candidate
    7. deriving the full real branch list
    8. composing the lower-level runtime owners needed for that stage work
    9. composing bootstrap-local helpers when needed
    10. composing repository_runtime.git helpers when needed
    11. composing the caller-supplied shell dependency

    Must not own:
    1. project-row writes
    2. commit / rollback behavior
    3. route or UI redirect decisions
    4. verification reporting
    5. repair policy
    6. low-level git command semantics already owned by repository_runtime.git
    7. persistent-shell lifecycle/state semantics already owned by ProjectShell
    
    
    project_paths:
        projects_base_directory
        project_directory
        project_repo_directory
        project_ssh_directory
        private_key_path
        public_key_path
    """

    from repository_runtime.git import clone_repo
    projects_base_directory = project_paths["projects_base_directory"]
    project_directory = project_paths["project_directory"]
    project_repo_directory = project_paths["project_repo_directory"]
    project_ssh_directory = project_paths["project_ssh_directory"]
    private_key_path = project_paths["private_key_path"]
    public_key_path = project_paths["public_key_path"]

    from repository_runtime.bootstrap import _verify_bs1
    # Should likely ensure with verification of bs1, even though this creates duplicate behavior.
    # Even though it has "possibly" - almost certainly - occurred in the exact same called origin just before bs2 execution


def _verify_bs2(
    *,
    project_paths: dict[str, Path],
    shell: ProjectShell | None,
) -> tuple[bool, None]:
    return True, None
