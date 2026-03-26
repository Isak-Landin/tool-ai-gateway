from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.models import Project
from db.session import SessionLocal
from errors import BoundProjectRuntimePersistenceError


class BoundProjectRuntimePersistence:
    def __init__(self, db_connection=None):
        self.db_connection = db_connection

    def get_bound_project_runtime_fields(self, project_id: int) -> dict | None:
        """
        Expected usage:
        - called by runtime binding / bound-runtime construction only
        - return the fields needed to construct a usable project runtime object
        - may later replace or extend the current bound-runtime persistence helper
        """
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project).where(Project.project_id == project_id)
            project = session.execute(stmt).scalar_one_or_none()
            if project is None:
                return None

            return {
                "project_id": project.project_id,
                "name": project.name,
                "ai_model_name": project.ai_model_name,
                "repo_path": project.repo_path,
                "remote_repo_url": project.remote_repo_url,
                "branch": project.branch,
                "ssh_key": project.ssh_key,
                "public_key_path": project.public_key_path,
            }
        except SQLAlchemyError as e:
            raise BoundProjectRuntimePersistenceError(
                str(e),
                field="project_id",
                error_type="sql error",
                file_id=__file__,
            ) from e
        finally:
            if self.db_connection is None:
                session.close()
