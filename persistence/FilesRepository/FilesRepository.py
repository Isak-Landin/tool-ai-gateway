from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.models import File
from db.session import SessionLocal
from errors import RepositoryFilePersistenceError


class FilesRepository:
    """
    Persistence-facing repository for project file rows.

    This surface is intentionally storage-shaped. It does not own live repository
    tree/file serving during runtime.
    """

    def __init__(self, db_connection=None, project_id: int | None = None, repo_path: str | None = None):
        self.db_connection = db_connection
        self.project_id = project_id
        self.repo_path = repo_path

    def _require_project_id(self) -> int:
        if self.project_id is None:
            raise RepositoryFilePersistenceError("project_id is required for file persistence")

        return self.project_id

    def _normalize_repo_path(self, relative_repo_path: str) -> str:
        normalized_path = str(relative_repo_path or "").strip()
        if not normalized_path:
            raise RepositoryFilePersistenceError("relative_repo_path is required")

        if normalized_path in {".", "/"}:
            raise RepositoryFilePersistenceError("file path must point to a file, not the repository root")

        return "/" + normalized_path.lstrip("/")

    def _serialize_row(self, row: File) -> dict:
        return {
            "id": row.id,
            "project_id": row.project_id,
            "message_id": row.message_id,
            "path": row.path,
            "name": row.name,
            "content": row.content,
            "total_lines": row.total_lines,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def list_by_project(self) -> list[dict]:
        project_id = self._require_project_id()
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(File).where(File.project_id == project_id).order_by(File.path.asc())
            rows = session.execute(stmt).scalars().all()
            return [self._serialize_row(row) for row in rows]
        except SQLAlchemyError as e:
            raise RepositoryFilePersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()

    def get_by_path(self, relative_repo_path: str) -> dict | None:
        project_id = self._require_project_id()
        normalized_path = self._normalize_repo_path(relative_repo_path)
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(File).where(
                File.project_id == project_id,
                File.path == normalized_path,
            )
            row = session.execute(stmt).scalar_one_or_none()
            if row is None:
                return None

            return self._serialize_row(row)
        except SQLAlchemyError as e:
            raise RepositoryFilePersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()

    def upsert_file(
        self,
        relative_repo_path: str,
        *,
        name: str | None = None,
        content: str | None = None,
        total_lines: int | None = None,
        message_id: int | None = None,
    ) -> dict:
        project_id = self._require_project_id()
        normalized_path = self._normalize_repo_path(relative_repo_path)
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(File).where(
                File.project_id == project_id,
                File.path == normalized_path,
            )
            row = session.execute(stmt).scalar_one_or_none()
            if row is None:
                row = File(
                    project_id=project_id,
                    path=normalized_path,
                )
                session.add(row)

            row.path = normalized_path
            row.name = name
            row.content = content
            row.total_lines = total_lines
            row.message_id = message_id

            session.flush()
            if self.db_connection is None:
                session.commit()

            session.refresh(row)
            return self._serialize_row(row)
        except SQLAlchemyError as e:
            if self.db_connection is None:
                session.rollback()
            raise RepositoryFilePersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()

    def delete_by_path(self, relative_repo_path: str) -> bool:
        project_id = self._require_project_id()
        normalized_path = self._normalize_repo_path(relative_repo_path)
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(File).where(
                File.project_id == project_id,
                File.path == normalized_path,
            )
            row = session.execute(stmt).scalar_one_or_none()
            if row is None:
                return False

            session.delete(row)
            if self.db_connection is None:
                session.commit()

            return True
        except SQLAlchemyError as e:
            if self.db_connection is None:
                session.rollback()
            raise RepositoryFilePersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()
