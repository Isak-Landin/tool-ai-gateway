"""
Internal rules for project persistence and bootstrap entry.

Ownership:
- This object owns project-row reads/writes and the persistence-layer entry into
  bootstrap stage work.
- This file owns project-path derivation and bootstrap-error translation for
  project creation.
- This file does not own bootstrap stage internals, repository transport
  behavior, or execution/runtime binding behavior.

Rule-set split:
- Internal helper rules apply to path derivation, bootstrap-error translation,
  and row serialization helpers.
- Encapsulated/public method rules apply to exposed project persistence methods.

Internal helper rules:
- Project creation must keep persistence validation, project-row creation,
  caller-owned bootstrap inputs, bootstrap invocation, persistence commit, and
  persisted-value verification as distinct visible stages.
- Bootstrap work must enter through the appropriate bootstrap stage entrypoint
  with caller-supplied resolved values and caller-owned shell dependencies.
- Bootstrap-layer errors must be translated through
  `_translate_project_bootstrap_error_for_persistence(...)`
  before leaving this file as persistence-layer failures.

Encapsulated/public method rules:
- `create_project(...)` is the bootstrap-entry persistence method for the current
  flow and should compose project-row creation with the relevant bootstrap stage
  entrypoint.
- Read/update methods should stay persistence-shaped and must not grow into
  runtime binding, execution, or repository transport ownership.
"""

import os
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.session import SessionLocal
from db.models import Project
from errors import ProjectBootstrapError, ProjectPersistenceError
from repository_runtime.bootstrap import bs1
from repository_runtime.shell import ProjectShell


DEFAULT_PROJECTS_ROOT = "/srv/tool-ai-gateway/projects"


def _derive_project_name_for_storage_path(name: str) -> str:
    """Normalize a project name into a filesystem-safe slug.

    Args:
        name: Raw project name to normalize for on-disk path construction.

    Returns:
        str: Lowercase slug suitable for project storage paths.
    """
    normalized_name = re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower()).strip("-")
    return normalized_name or "project"


def _require_projects_root_for_bootstrap() -> Path:
    """Load the configured projects root directory from environment settings.

    Args:
        None.

    Returns:
        Path: Expanded filesystem path for the projects root directory.
    """
    configured_root = str(os.getenv("PROJECTS_ROOT", DEFAULT_PROJECTS_ROOT)).strip()
    if not configured_root:
        raise ProjectPersistenceError(
            "PROJECTS_ROOT is required for project bootstrap",
            field="PROJECTS_ROOT",
            error_type="missing configuration",
            file_id=__file__,
        )

    return Path(configured_root).expanduser()


def _derive_project_storage_paths_for_bootstrap(
    project_id: int,
    project_name: str,
) -> dict[str, Path]:
    """Build the filesystem paths used during project bootstrap.

    Args:
        project_id: Persisted project identifier used to make the path unique.
        project_name: Human-readable project name used in the storage slug.

    Returns:
        dict[str, Path]: Named filesystem paths required for project bootstrap. Referenced internally as project_path:
        {
            "projects_base_directory": projects_base_directory,
            "project_directory": project_directory,
            "project_repo_directory": project_directory / "repo",
            "project_ssh_directory": project_ssh_directory,
            "private_key_path": project_ssh_directory / "id_ed25519",
            "public_key_path": project_ssh_directory / "id_ed25519.pub",
        }

    """
    if project_id is None:
        raise ProjectPersistenceError(
            "project_id is required before project storage paths can be built",
            field="project_id",
            error_type="missing project id",
            file_id=__file__,
        )

    projects_base_directory = _require_projects_root_for_bootstrap()
    project_directory = projects_base_directory / f"{_derive_project_name_for_storage_path(project_name)}-{project_id}"
    project_ssh_directory = project_directory / "ssh"
    return {
        "projects_base_directory": projects_base_directory,
        "project_directory": project_directory,
        "project_repo_directory": project_directory / "repo",
        "project_ssh_directory": project_ssh_directory,
        "private_key_path": project_ssh_directory / "id_ed25519",
        "public_key_path": project_ssh_directory / "id_ed25519.pub",
    }


def _translate_project_bootstrap_error_for_persistence(
    error: ProjectBootstrapError,
) -> ProjectPersistenceError:
    """Translate bootstrap-layer errors into project-persistence errors.

    Args:
        error: Bootstrap-layer exception raised during project creation work.

    Returns:
        ProjectPersistenceError: Persistence-shaped error carrying translated metadata.
    """
    return ProjectPersistenceError(
        str(error),
        field=getattr(error, "field", None),
        error_type=getattr(error, "error_type", None),
        file_id=str(getattr(error, "file_id", __file__)),
    )


class ProjectPersistence:
    """Persistence owner for project entity reads, writes, and bootstrap entry."""

    def __init__(self, db_connection=None):
        """Create the project persistence helper.

        Args:
            db_connection: Optional SQLAlchemy session/connection supplied by a caller.

        Returns:
            None: The helper stores the DB dependency for later operations.
        """
        self.db_connection = db_connection

    def _serialize_project_for_route_response(self, row: Project) -> dict:
        """Serialize one project ORM row into the route-facing return shape.

        Args:
            row: SQLAlchemy `Project` row to serialize.

        Returns:
            dict: Serialized project payload used by project routes.
        """
        return {
            "project_id": row.project_id,
            "name": row.name,
            "branch": row.branch,
            "branches": list(row.branches or []),
            "remote_repo_url": row.remote_repo_url,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def get_project_by_id(self, project_id: int) -> dict | None:
        """Load one persisted project by its project id.

        Args:
            project_id: Persisted project identifier to load.

        Returns:
            dict | None: Serialized project row when found, otherwise `None`.
        """
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project).where(Project.project_id == project_id)
            result = session.execute(stmt).scalar_one_or_none()

            if result is None:
                return None

            return self._serialize_project_for_route_response(result)
        except SQLAlchemyError as e:
            raise ProjectPersistenceError(str(e), file_id=__file__) from e
        finally:
            if self.db_connection is None and session:
                session.close()

    def create_project(self, name, remote_repo_url):
        """Create a new project row and bootstrap its local storage/keypair.

        Args:
            name: Human-readable project name to persist.
            remote_repo_url: Remote repository URL to associate with the project.

        Returns:
            dict: Created project payload including the generated public key.
        """
        session = self.db_connection or SessionLocal()
        shell: ProjectShell | None = None
        try:
            normalized_name = str(name).strip()
            if not normalized_name:
                raise ProjectPersistenceError(
                    "name is required",
                    field="name",
                    error_type="missing value",
                    file_id=__file__,
                )

            normalized_remote_repo_url = str(remote_repo_url).strip()
            if not normalized_remote_repo_url:
                raise ProjectPersistenceError(
                    "remote_repo_url is required",
                    field="remote_repo_url",
                    error_type="missing value",
                    file_id=__file__,
                )

            remote_repo_result = session.execute(
                select(Project).where(Project.remote_repo_url == normalized_remote_repo_url)
            ).scalar_one_or_none()
            if remote_repo_result:
                raise ProjectPersistenceError(
                    "Remote repository URL already exists",
                    field="remote_repo_url",
                    error_type="duplicate",
                    file_id=__file__,
                )

            new_project = Project(name=normalized_name, remote_repo_url=normalized_remote_repo_url)
            session.add(new_project)
            session.flush()

            project_paths = _derive_project_storage_paths_for_bootstrap(
                project_id=new_project.project_id,
                project_name=new_project.name,
            )
            shell = ProjectShell()
            bs1(
                project_paths=project_paths,
                project_id=new_project.project_id,
                shell=shell,
            )

            new_project.repo_path = str(project_paths["project_repo_directory"])
            new_project.ssh_key = str(project_paths["private_key_path"])
            new_project.public_key_path = str(project_paths["public_key_path"])
            session.commit()

            try:
                public_key = project_paths["public_key_path"].read_text(encoding="utf-8").strip()
            except OSError as e:
                raise ProjectPersistenceError(
                    f"Failed to read generated public key: {e}",
                    field="public_key_path",
                    error_type="key read failed",
                    file_id=__file__,
                ) from e

            if not public_key:
                raise ProjectPersistenceError(
                    "Generated public key is empty",
                    field="public_key_path",
                    error_type="key generation failed",
                    file_id=__file__,
                )

            return {
                "project_id": new_project.project_id,
                "name": new_project.name,
                "remote_repo_url": new_project.remote_repo_url,
                "public_key": public_key,
            }
        except ProjectBootstrapError as e:
            session.rollback()
            raise _translate_project_bootstrap_error_for_persistence(e) from e
        except ProjectPersistenceError:
            session.rollback()
            raise
        except SQLAlchemyError as e:
            session.rollback()
            raise ProjectPersistenceError(
                str(e),
                error_type="sql error",
                file_id=__file__,
            ) from e
        finally:
            if shell is not None:
                shell.close()
            if self.db_connection is None and session:
                session.close()

    def list_all_projects(self) -> list[dict]:
        """List all persisted projects ordered from newest to oldest.

        Args:
            None.

        Returns:
            list[dict]: Serialized project rows for all persisted projects.
        """
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project).order_by(Project.created_at.desc())
            results = session.execute(stmt).scalars().all()
            return [self._serialize_project_for_route_response(result) for result in results]
        except SQLAlchemyError as e:
            raise ProjectPersistenceError(str(e), file_id=__file__) from e
        finally:
            if self.db_connection is None and session:
                session.close()

    def update_project(self, project_id: int, *, name: str | None = None, branch: str | None = None) -> dict | None:
        """Update mutable project fields for an existing persisted project.

        Args:
            project_id: Persisted project identifier to update.
            name: Optional replacement project name when the caller wants to rename.
            branch: Optional replacement branch value when the caller wants to retarget.

        Returns:
            dict | None: Serialized updated project row when found, otherwise `None`.
        """
        if project_id is None:
            raise ProjectPersistenceError(
                "project_id is required",
                field="project_id",
                error_type="missing project id",
                file_id=__file__,
            )

        updates: dict[str, str] = {}
        if name is not None:
            normalized_name = str(name).strip()
            if not normalized_name:
                raise ProjectPersistenceError(
                    "name must not be blank",
                    field="name",
                    error_type="missing value",
                    file_id=__file__,
                )
            updates["name"] = normalized_name

        if branch is not None:
            normalized_branch = str(branch).strip()
            if not normalized_branch:
                raise ProjectPersistenceError(
                    "branch must not be blank",
                    field="branch",
                    error_type="missing value",
                    file_id=__file__,
                )
            updates["branch"] = normalized_branch

        if not updates:
            raise ProjectPersistenceError(
                "at least one mutable project field is required",
                field="project",
                error_type="missing value",
                file_id=__file__,
            )

        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project).where(Project.project_id == project_id)
            project_row = session.execute(stmt).scalar_one_or_none()
            if project_row is None:
                return None

            for field_name, field_value in updates.items():
                setattr(project_row, field_name, field_value)

            session.flush()
            if self.db_connection is None:
                session.commit()

            session.refresh(project_row)
            return self._serialize_project_for_route_response(project_row)
        except SQLAlchemyError as e:
            if self.db_connection is None:
                session.rollback()
            raise ProjectPersistenceError(str(e), file_id=__file__) from e
        finally:
            if self.db_connection is None and session:
                session.close()
