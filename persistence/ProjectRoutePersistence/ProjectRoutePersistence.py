from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.session import SessionLocal
from db.models import Project
from errors import PersistenceError



class ProjectRoutePersistence:
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
                "ai_model_name": result.ai_model_name,
                "orchestrator_name": result.orchestrator_name,
                "repo_path": result.repo_path,
                "remote_repo_url": result.remote_repo_url,
                "branch": result.branch,
                "ssh_key": result.ssh_key,
                "created_at": result.created_at,
            }
        except SQLAlchemyError as e:
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None and session:
                session.close()

    def create_project(self, name, remote_repo_url, ssh_key):
        session = self.db_connection or SessionLocal()
        try:
            # Check for duplicate remote_repo_url
            remote_repo_result = session.execute(
                select(Project).where(Project.remote_repo_url == remote_repo_url)
            ).scalar_one_or_none()
            if remote_repo_result:
                raise PersistenceError("Remote repository URL already exists", field="remote_repo_url", error_type="duplicate")

            # Check for duplicate ssh_key
            ssh_key_result = session.execute(
                select(Project).where(Project.ssh_key == ssh_key)
            ).scalar_one_or_none()
            if ssh_key_result:
                raise PersistenceError("SSH key already registered", field="ssh_key", error_type="duplicate")

            # Create project
            new_project = Project(name=name, remote_repo_url=remote_repo_url, ssh_key=ssh_key)
            session.add(new_project)
            session.commit()

            return {
                "project_id": new_project.project_id,
                "name": new_project.name,
                "remote_repo_url": new_project.remote_repo_url,
                "ssh_key": new_project.ssh_key,
            }
        except PersistenceError:
            session.rollback()
            raise
        except SQLAlchemyError as e:
            session.rollback()
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None and session:
                session.close()

    def list_all_projects(self) -> list[dict]:
        """
        Pattern: Similar to get_project_by_id and create_project
        - Get session
        - Try: execute SELECT query without WHERE clause
        - Return list of dicts with project info
        - Handle SQLAlchemyError
        - Finally: close session if needed
        """
        session = self.db_connection or SessionLocal()
        try:
            # Query all projects (no WHERE clause)
            # Should query ALL fields needed
            stmt = select(Project)  # Get full Project objects
            results = session.execute(stmt).scalars().all()  # Use .scalars().all()
            return [
                {
                    "project_id": r.project_id,
                    "name": r.name,
                    "ai_model_name": r.ai_model_name,
                    "orchestrator_name": r.orchestrator_name,
                    "created_at": r.created_at
                    # Add any other fields needed
                }
                for r in results
            ]
        except SQLAlchemyError as e:
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None and session:
                session.close()


class ProjectsRepository(ProjectRoutePersistence):
    """Compatibility alias for existing route-level callers."""