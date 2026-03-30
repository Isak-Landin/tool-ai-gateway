from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.models import Message
from db.session import SessionLocal
from errors import MessageHistoryPersistenceError


class MessagesRepository:
    def __init__(self, db_connection=None, project_id: int | None = None):
        self.db_connection = db_connection
        self.project_id = project_id

    def _require_project_id(self) -> int:
        if self.project_id is None:
            raise MessageHistoryPersistenceError("project_id is required for message history persistence")

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
            "ai_model_name": row.ai_model_name,
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

    def list_by_project(
        self,
        *,
        limit: int | None = None,
        before_sequence_no: int | None = None,
        after_sequence_no: int | None = None,
    ) -> list[dict]:
        project_id = self._require_project_id()
        session = self.db_connection or SessionLocal()
        try:
            stmt = (
                select(Message)
                .where(Message.project_id == project_id)
                .order_by(Message.sequence_no.asc())
            )

            if before_sequence_no is not None:
                stmt = stmt.where(Message.sequence_no < before_sequence_no)

            if after_sequence_no is not None:
                stmt = stmt.where(Message.sequence_no > after_sequence_no)

            if limit is not None:
                if limit < 1:
                    raise MessageHistoryPersistenceError("limit must be >= 1")
                stmt = stmt.limit(limit)

            rows = session.execute(stmt).scalars().all()
            return [self._serialize_message_row(row) for row in rows]
        except SQLAlchemyError as e:
            raise MessageHistoryPersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()

    def get_by_sequence_no(self, sequence_no: int) -> dict | None:
        project_id = self._require_project_id()
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(Message).where(
                Message.project_id == project_id,
                Message.sequence_no == sequence_no,
            )
            row = session.execute(stmt).scalar_one_or_none()
            if row is None:
                return None

            return self._serialize_message_row(row)
        except SQLAlchemyError as e:
            raise MessageHistoryPersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()

    def insert_message(self, message_data: dict) -> dict:
        session = self.db_connection or SessionLocal()
        try:
            payload = dict(message_data)
            if "project_id" not in payload:
                payload["project_id"] = self._require_project_id()

            message = Message(**payload)
            session.add(message)
            session.flush()
            if self.db_connection is None:
                session.commit()
            session.refresh(message)

            return self._serialize_message_row(message)
        except SQLAlchemyError as e:
            if self.db_connection is None:
                session.rollback()
            raise MessageHistoryPersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()
