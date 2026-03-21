from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from db.session import SessionLocal
from db.models import Project, Message, File
from errors import PersistenceError





class ProjectsRepository:
    def __init__(self, db_connection=None):
        self.db_connection = db_connection

    def get_project_by_id(self, project_id: int) -> dict | None:
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Project).where(Project.id == project_id)
            result = session.execute(stmt).scalar_one_or_none()

            if result is None:
                return None

            return {
                "id": result.id,
                "name": result.name,
                "ai_model_name": result.ai_model_name,
                "orchestrator_name": result.orchestrator_name,
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
                raise PersistenceError("Remote repository URL already exists", field="remote_repo_url")

            # Check for duplicate ssh_key
            ssh_key_result = session.execute(
                select(Project).where(Project.ssh_key == ssh_key)
            ).scalar_one_or_none()
            if ssh_key_result:
                raise PersistenceError("SSH key already registered", field="ssh_key")

            # Create project
            new_project = Project(name=name, remote_repo_url=remote_repo_url, ssh_key=ssh_key)
            session.add(new_project)
            session.commit()

            return {
                "project_id": new_project.id,
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
                    "id": r.id,
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






class MessagesRepository:
    def __init__(self, db_connection=None, project_id: int | None = None):
        self.db_connection = db_connection
        self.project_id = project_id

    def list_by_project(self) -> list[dict]:
        session = self.db_connection or SessionLocal()
        try:
            stmt = (
                select(Message)
                .where(Message.project_id == self.project_id)
                .order_by(Message.sequence_no)
            )

            rows = session.execute(stmt).scalars().all()

            return [
                {
                    "id": r.id,
                    "project_id": r.project_id,
                    "sequence_no": r.sequence_no,
                    "role": r.role,
                    "content": r.content,
                    "thinking": r.thinking,
                    "tool_name": r.tool_name,
                    "tool_calls_json": r.tool_calls_json,
                    "images_json": r.images_json,
                    "created_at": r.created_at,
                }
                for r in rows
            ]

        except SQLAlchemyError as e:
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None:
                session.close()

    def insert_message(self, message_data: dict) -> dict:
        session = self.db_connection or SessionLocal()
        try:
            message = Message(**message_data)
            session.add(message)
            session.commit()
            session.refresh(message)

            return {
                "id": message.id,
                "project_id": message.project_id,
                "sequence_no": message.sequence_no,
                "role": message.role,
                "content": message.content,
                "thinking": message.thinking,
            }

        except SQLAlchemyError as e:
            session.rollback()
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None:
                session.close()


class FilesRepository:
    def __init__(self, db_connection=None, project_id: int | None = None):
        self.db_connection = db_connection
        self.project_id = project_id

    def list_by_project(self) -> list[dict]:
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(File).where(File.project_id == self.project_id)
            rows = session.execute(stmt).scalars().all()

            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "content": r.content,
                    "project_id": r.project_id,
                }
                for r in rows
            ]

        except SQLAlchemyError as e:
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None:
                session.close()

    def search_files(self, query: str) -> list[dict]:
        raise NotImplementedError("search_files is not implemented yet")

    def get_file(self, file_id: int) -> dict | None:
        raise NotImplementedError("get_file is not implemented yet")