from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from db.models import Message
from db.session import SessionLocal
from errors import ExecutionPersistenceError
from repository_tools.common import get_repository_relative_path, resolve_repository_target


class ExecutionPersistence:
    def __init__(self, db_connection=None, project_id: int | None = None, repo_path: str | None = None):
        self.db_connection = db_connection
        self.project_id = project_id
        self.repo_path = repo_path

    def _require_project_id(self) -> int:
        if self.project_id is None:
            raise ExecutionPersistenceError(
                "project_id is required for execution persistence",
                field="project_id",
                error_type="missing project id",
                file_id=__file__,
            )

        return self.project_id

    def _serialize_message_row(self, row: Message) -> dict:
        return {
            "id": row.id,
            "project_id": row.project_id,
            "sequence_no": row.sequence_no,
            "role": row.role,
            "content": row.content,
            "thinking": row.thinking,
            "tool_name": row.tool_name,
            "tool_calls_json": row.tool_calls_json,
            "images_json": row.images_json,
            "ollama_model": row.ollama_model,
            "ollama_created_at": row.ollama_created_at,
            "done": row.done,
            "done_reason": row.done_reason,
            "total_duration": row.total_duration,
            "load_duration": row.load_duration,
            "prompt_eval_count": row.prompt_eval_count,
            "prompt_eval_duration": row.prompt_eval_duration,
            "eval_count": row.eval_count,
            "eval_duration": row.eval_duration,
            "raw_message_json": row.raw_message_json,
            "raw_response_json": row.raw_response_json,
            "created_at": row.created_at,
        }

    def _require_repo_path(self) -> str:
        if not str(self.repo_path).strip():
            raise ExecutionPersistenceError(
                "repo_path is required for execution selected context",
                field="repo_path",
                error_type="missing repo path",
                file_id=__file__,
            )

        return str(self.repo_path)

    def _serialize_selected_context_file(self, repo_root: Path, target_path: Path, content: str) -> dict:
        return {
            "name": target_path.name,
            "path": get_repository_relative_path(repo_root, target_path),
            "content": content,
        }

    def load_recent_history(
        self,
        limit: int,
        before_sequence_no: int | None = None,
    ) -> list[dict]:
        """
        Load a bounded recent project history window in execution-ready order.
        """
        project_id = self._require_project_id()

        if limit < 1:
            raise ExecutionPersistenceError(
                "limit must be >= 1",
                field="limit",
                error_type="invalid value",
                file_id=__file__,
            )

        session = self.db_connection or SessionLocal()
        try:
            stmt = (
                select(Message)
                .where(Message.project_id == project_id)
                .order_by(Message.sequence_no.desc())
                .limit(limit)
            )

            if before_sequence_no is not None:
                stmt = stmt.where(Message.sequence_no < before_sequence_no)

            rows = session.execute(stmt).scalars().all()
            rows = list(reversed(rows))

            return [self._serialize_message_row(row) for row in rows]
        except SQLAlchemyError as e:
            raise ExecutionPersistenceError(
                str(e),
                field="",
                error_type="sql error",
                file_id=__file__,
            )
        finally:
            if self.db_connection is None:
                session.close()

    def store_artifact(self, artifact_data: dict) -> dict:
        """
        Persist one execution-owned message or tool artifact.
        """
        project_id = self._require_project_id()

        session = self.db_connection or SessionLocal()
        try:
            payload = dict(artifact_data)
            payload["project_id"] = project_id

            artifact = Message(**payload)
            session.add(artifact)
            session.commit()
            session.refresh(artifact)

            return self._serialize_message_row(artifact)
        except SQLAlchemyError as e:
            session.rollback()
            raise ExecutionPersistenceError(
                str(e),
                field="",
                error_type="sql error",
                file_id=__file__,
            )
        finally:
            if self.db_connection is None:
                session.close()

    def load_selected_context(self, selected_files: list[str]) -> list[dict]:
        """
        Load selected file context from the current local repository state in caller order.
        """
        if not selected_files:
            return []

        selected_paths = [str(selected_file).strip() for selected_file in selected_files if str(selected_file).strip()]
        if not selected_paths:
            return []

        repo_path = self._require_repo_path()
        selected_context_rows: list[dict] = []

        for selected_path in selected_paths:
            try:
                repo_root, target_path = resolve_repository_target(
                    repo_path=repo_path,
                    relative_repo_path=selected_path,
                )
            except ValueError as e:
                raise ExecutionPersistenceError(
                    str(e),
                    field="selected_files",
                    error_type="invalid selected path",
                    file_id=__file__,
                ) from e

            if not target_path.is_file():
                raise ExecutionPersistenceError(
                    f"Selected path is not a file in repository: {get_repository_relative_path(repo_root, target_path)}",
                    field="selected_files",
                    error_type="invalid selected path",
                    file_id=__file__,
                )

            try:
                file_content = target_path.read_text(encoding="utf-8")
            except OSError as e:
                raise ExecutionPersistenceError(
                    str(e),
                    field="selected_files",
                    error_type="file read error",
                    file_id=__file__,
                ) from e

            selected_context_rows.append(
                self._serialize_selected_context_file(
                    repo_root=repo_root,
                    target_path=target_path,
                    content=file_content,
                )
            )

        return selected_context_rows

    def load_next_sequence_no(self) -> int:
        """
        Load the next sequence number without making execution ordering implicit.
        """
        project_id = self._require_project_id()

        session = self.db_connection or SessionLocal()
        try:
            stmt = select(func.max(Message.sequence_no)).where(Message.project_id == project_id)
            current_max = session.execute(stmt).scalar_one_or_none()
            return (current_max or 0) + 1
        except SQLAlchemyError as e:
            raise ExecutionPersistenceError(
                str(e),
                field="",
                error_type="sql error",
                file_id=__file__,
            )
        finally:
            if self.db_connection is None:
                session.close()
