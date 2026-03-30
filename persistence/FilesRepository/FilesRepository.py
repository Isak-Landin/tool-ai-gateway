from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.models import File
from db.session import SessionLocal
from errors import RepositoryFilePersistenceError
from repository_tools import normalize_repository_relative_path


class FilesRepository:
    """
    Persistence-facing repository for project file rows.

    This surface is intentionally storage-shaped. It does not own live repository
    tree/file serving during runtime.
    """

    def __init__(self, db_connection=None, project_id: int | None = None):
        """Create the storage-shaped file repository for one project scope.

        Args:
            db_connection: Optional SQLAlchemy session/connection supplied by a caller.
            project_id: Optional persisted project identifier for all repository operations.

        Returns:
            None: The repository stores the DB dependency and project scope.
        """
        self.db_connection = db_connection
        self.project_id = project_id

    def _require_project_id(self) -> int:
        """Return the configured project id or fail when it is missing.

        Args:
            None.

        Returns:
            int: Persisted project identifier for file-row operations.
        """
        if self.project_id is None:
            raise RepositoryFilePersistenceError("project_id is required for file persistence")

        return self.project_id

    def _normalize_repo_path(self, relative_repo_path: str) -> str:
        """Normalize a repo-relative path for persistence storage.

        Args:
            relative_repo_path: Repo-relative file path provided by the caller.

        Returns:
            str: Normalized repo-relative file path.
        """
        try:
            return normalize_repository_relative_path(relative_repo_path, allow_root=False)
        except ValueError as e:
            raise RepositoryFilePersistenceError(str(e)) from e

    def _serialize_row(self, row: File) -> dict:
        """Serialize one file ORM row into the repository return shape.

        Args:
            row: SQLAlchemy `File` row to serialize.

        Returns:
            dict: Storage-shaped file-row payload.
        """
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

    def _raise_live_file_runtime_deprecation(self, method_name: str) -> None:
        """Fail when callers try to use file storage as a live file owner.

        Args:
            method_name: Deprecated method name the caller attempted to use.

        Returns:
            Never: This helper always raises a repository file persistence error.
        """
        raise RepositoryFilePersistenceError(
            f"FilesRepository.{method_name} is deprecated for live file/tree access; use the bound FileRuntime surface"
        )

    def _raise_storage_api_deprecation(self, method_name: str, explicit_method_name: str) -> None:
        """Fail when callers use deprecated ambiguous storage method names.

        Args:
            method_name: Deprecated method name the caller attempted to use.
            explicit_method_name: Supported storage-shaped method name to use instead.

        Returns:
            Never: This helper always raises a repository file persistence error.
        """
        raise RepositoryFilePersistenceError(
            f"FilesRepository.{method_name} is deprecated because it blurs persistence ownership; use "
            f"FilesRepository.{explicit_method_name} for storage-shaped access or FileRuntime for live file/tree access"
        )

    def load_selected_context(self, selected_files: list[str]) -> list[dict]:
        """Reject deprecated live selected-context access on file persistence.

        Args:
            selected_files: Repo-relative file paths requested by the caller.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("load_selected_context")

    def list_tree(self, relative_repo_path: str | None = None) -> list[dict]:
        """Reject deprecated live tree access on file persistence.

        Args:
            relative_repo_path: Optional repo-relative directory path requested by the caller.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("list_tree")

    def read_file(
        self,
        relative_repo_path: str,
        start_line: int | None = None,
        number_of_lines: int | None = None,
        end_line: int | None = None,
    ) -> dict:
        """Reject deprecated live file access on file persistence.

        Args:
            relative_repo_path: Repo-relative file path requested by the caller.
            start_line: Optional first line number to include.
            number_of_lines: Optional count of lines to include from `start_line`.
            end_line: Optional inclusive last line number to include.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("read_file")

    def search_text(
        self,
        query: str,
        relative_repo_path: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> list[dict]:
        """Reject deprecated live text-search access on file persistence.

        Args:
            query: Search query the caller attempted to run.
            relative_repo_path: Optional repo-relative path to limit the search scope.
            case_sensitive: Whether the attempted search preserved letter case.
            max_results: Maximum number of matches the caller requested.

        Returns:
            Never: This method always raises to enforce FileRuntime usage.
        """
        self._raise_live_file_runtime_deprecation("search_text")

    def list_by_project(self) -> list[dict]:
        """Reject deprecated ambiguous list method on file persistence.

        Args:
            None.

        Returns:
            Never: This method always raises to direct callers to `list_file_rows`.
        """
        self._raise_storage_api_deprecation("list_by_project", "list_file_rows")

    def get_by_path(self, relative_repo_path: str) -> dict | None:
        """Reject deprecated ambiguous lookup method on file persistence.

        Args:
            relative_repo_path: Repo-relative file path requested by the caller.

        Returns:
            Never: This method always raises to direct callers to `get_file_row_by_path`.
        """
        self._raise_storage_api_deprecation("get_by_path", "get_file_row_by_path")

    def upsert_file(
        self,
        relative_repo_path: str,
        *,
        name: str | None = None,
        content: str | None = None,
        total_lines: int | None = None,
        message_id: int | None = None,
    ) -> dict:
        """Reject deprecated ambiguous upsert method on file persistence.

        Args:
            relative_repo_path: Repo-relative file path requested by the caller.
            name: Optional file name to persist.
            content: Optional file content snapshot to persist.
            total_lines: Optional total line count to persist.
            message_id: Optional related message id for provenance.

        Returns:
            Never: This method always raises to direct callers to `upsert_file_row`.
        """
        self._raise_storage_api_deprecation("upsert_file", "upsert_file_row")

    def delete_by_path(self, relative_repo_path: str) -> bool:
        """Reject deprecated ambiguous delete method on file persistence.

        Args:
            relative_repo_path: Repo-relative file path requested by the caller.

        Returns:
            Never: This method always raises to direct callers to `delete_file_row_by_path`.
        """
        self._raise_storage_api_deprecation("delete_by_path", "delete_file_row_by_path")

    def list_file_rows(self) -> list[dict]:
        """List persisted file rows for the configured project.

        Args:
            None.

        Returns:
            list[dict]: Serialized persisted file rows ordered by path.
        """
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

    def get_file_row_by_path(self, relative_repo_path: str) -> dict | None:
        """Load one persisted file row by repo-relative path.

        Args:
            relative_repo_path: Repo-relative file path to look up in persistence.

        Returns:
            dict | None: Serialized file row when found, otherwise `None`.
        """
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

    def upsert_file_row(
        self,
        relative_repo_path: str,
        *,
        name: str | None = None,
        content: str | None = None,
        total_lines: int | None = None,
        message_id: int | None = None,
    ) -> dict:
        """Insert or update one persisted file row for the configured project.

        Args:
            relative_repo_path: Repo-relative file path to store.
            name: Optional file name to persist with the row.
            content: Optional file content snapshot to persist.
            total_lines: Optional total line count to persist.
            message_id: Optional related message id for provenance.

        Returns:
            dict: Serialized stored file row after persistence completes.
        """
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

    def delete_file_row_by_path(self, relative_repo_path: str) -> bool:
        """Delete one persisted file row by repo-relative path.

        Args:
            relative_repo_path: Repo-relative file path to delete from persistence.

        Returns:
            bool: `True` when a row was deleted, otherwise `False`.
        """
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
