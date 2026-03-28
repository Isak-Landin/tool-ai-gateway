import os
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.session import SessionLocal
from db.models import Project
from errors import ProjectBootstrapError, ProjectPersistenceError
from repository_runtime.bootstrap import ProjectBootstrap


DEFAULT_PROJECTS_ROOT = "/srv/tool-ai-gateway/projects"


def _slugify_project_name(name: str) -> str:
    normalized_name = re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower()).strip("-")
    return normalized_name or "project"


def _get_projects_root() -> Path:
    configured_root = str(os.getenv("PROJECTS_ROOT", DEFAULT_PROJECTS_ROOT)).strip()
    if not configured_root:
        raise ProjectPersistenceError(
            "PROJECTS_ROOT is required for project bootstrap",
            field="PROJECTS_ROOT",
            error_type="missing configuration",
            file_id=__file__,
        )

    return Path(configured_root).expanduser()


def _build_project_storage_paths(project_id: int, project_name: str) -> dict[str, Path]:
    if project_id is None:
        raise ProjectPersistenceError(
            "project_id is required before project storage paths can be built",
            field="project_id",
            error_type="missing project id",
            file_id=__file__,
        )

    projects_root = _get_projects_root()
    project_root = projects_root / f"{_slugify_project_name(project_name)}-{project_id}"
    ssh_directory = project_root / "ssh"
    return {
        "projects_root": projects_root,
        "project_root": project_root,
        "repo_path": project_root / "repo",
        "ssh_directory": ssh_directory,
        "private_key_path": ssh_directory / "id_ed25519",
        "public_key_path": ssh_directory / "id_ed25519.pub",
    }


def _translate_bootstrap_error(error: ProjectBootstrapError) -> ProjectPersistenceError:
    return ProjectPersistenceError(
        str(error),
        field=getattr(error, "field", None),
        error_type=getattr(error, "error_type", None),
        file_id=getattr(error, "file_id", __file__),
    )


class ProjectPersistence:
    def __init__(self, db_connection=None):
        self.db_connection = db_connection

    def get_project_by_id(self, project_id: int) -> dict | None:
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project).where(Project.project_id == project_id)
            result = session.execute(stmt).scalar_one_or_none()

            if result is None:
                return None

            return {
                "project_id": result.project_id,
                "name": result.name,
                "branch": result.branch,
                "created_at": result.created_at,
            }
        except SQLAlchemyError as e:
            raise ProjectPersistenceError(str(e), file_id=__file__) from e
        finally:
            if self.db_connection is None and session:
                session.close()

    def create_project(self, name, remote_repo_url):
        session = self.db_connection or SessionLocal()
        project_root: Path | None = None
        bootstrap = ProjectBootstrap()
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

            if new_project.project_id is None:
                raise ProjectPersistenceError(
                    "Project row did not receive a project_id during bootstrap",
                    field="project_id",
                    error_type="missing project id",
                    file_id=__file__,
                )

            project_paths = _build_project_storage_paths(
                project_id=new_project.project_id,
                project_name=new_project.name,
            )
            project_root = project_paths["project_root"]
            bootstrap.create_project_storage(project_paths)
            public_key = bootstrap.generate_project_keypair(
                private_key_path=project_paths["private_key_path"],
                public_key_path=project_paths["public_key_path"],
                project_id=new_project.project_id,
            )

            new_project.repo_path = str(project_paths["repo_path"])
            new_project.ssh_key = str(project_paths["private_key_path"])
            new_project.public_key_path = str(project_paths["public_key_path"])
            session.commit()
            session.refresh(new_project)

            if new_project.repo_path != str(project_paths["repo_path"]):
                raise ProjectPersistenceError(
                    "Persisted repo_path does not match the bootstrapped repository path",
                    field="repo_path",
                    error_type="persist verification failed",
                    file_id=__file__,
                )

            if new_project.ssh_key != str(project_paths["private_key_path"]):
                raise ProjectPersistenceError(
                    "Persisted ssh_key does not match the bootstrapped private key path",
                    field="ssh_key",
                    error_type="persist verification failed",
                    file_id=__file__,
                )

            if new_project.public_key_path != str(project_paths["public_key_path"]):
                raise ProjectPersistenceError(
                    "Persisted public_key_path does not match the bootstrapped public key path",
                    field="public_key_path",
                    error_type="persist verification failed",
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
            bootstrap.cleanup_project_storage(project_root)
            raise _translate_bootstrap_error(e) from e
        except ProjectPersistenceError:
            session.rollback()
            bootstrap.cleanup_project_storage(project_root)
            raise
        except SQLAlchemyError as e:
            session.rollback()
            bootstrap.cleanup_project_storage(project_root)
            raise ProjectPersistenceError(
                str(e),
                error_type="sql error",
                file_id=__file__,
            ) from e
        finally:
            bootstrap.close()
            if self.db_connection is None and session:
                session.close()

    def list_all_projects(self) -> list[dict]:
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project)
            results = session.execute(stmt).scalars().all()
            return [
                {
                    "project_id": r.project_id,
                    "name": r.name,
                    "branch": r.branch,
                    "created_at": r.created_at,
                }
                for r in results
            ]
        except SQLAlchemyError as e:
            raise ProjectPersistenceError(str(e), file_id=__file__) from e
        finally:
            if self.db_connection is None and session:
                session.close()
