"""
Internal rules for message-row persistence.

Ownership:
- This object owns DB-backed message-row reads, writes, ordering, and storage-
  shaped error translation for one project scope.
- This object does not own higher-level route/execution history behavior.

Rule-set split:
- Internal method rules apply to project-scope validation, sequence validation,
  row serialization, and deprecation/error helpers.
- Encapsulated/public method rules apply to the exposed storage-shaped
  message-row methods and deprecated compatibility methods.

Internal method rules:
- Storage methods must resolve project scope through `_require_project_id()`
  before issuing persistence reads/writes.
- Sequence-sensitive methods must validate sequence numbers through
  `_validate_sequence_no(...)` before query construction.
- Deprecated shared-history or ambiguous methods must fail explicitly through
  the internal deprecation helper instead of behaving like message-runtime
  owners.

Encapsulated/public method rules:
- Storage-shaped methods should keep explicit persistence naming such as
  `list_message_rows(...)`, `get_message_row_by_sequence_no(...)`,
  `load_recent_message_rows(...)`, `load_next_message_sequence_no(...)`, and
  `store_message_artifact(...)`.
- Deprecated compatibility methods should continue to fail through the declared
  internal deprecation helper so callers do not harden around the wrong owner.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from db.models import Message
from db.session import SessionLocal
from errors import MessageHistoryPersistenceError


class MessagesRepository:
    """
    Persistence-facing repository for project message rows.

    This surface is intentionally storage-shaped. It owns message-row reads and
    writes, but it does not replace the MessageRuntime function surface used by
    routes and execution for higher-level message/history behavior.
    """

    def __init__(self, db_connection=None, project_id: int | None = None):
        """Create the storage-shaped message repository for one project scope.

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
            int: Persisted project identifier for message-row operations.
        """
        if self.project_id is None:
            raise MessageHistoryPersistenceError("project_id is required for message history persistence")

        return self.project_id

    def _validate_sequence_no(self, sequence_no: int, *, field_name: str) -> int:
        """Validate a positive message sequence number for repository work.

        Args:
            sequence_no: Sequence number value to validate.
            field_name: Field label to mention if validation fails.

        Returns:
            int: The validated sequence number.
        """
        if sequence_no < 1:
            raise MessageHistoryPersistenceError(f"{field_name} must be >= 1")

        return sequence_no

    def _serialize_message_row(self, row: Message) -> dict:
        """Serialize one message ORM row into the repository return shape.

        Args:
            row: SQLAlchemy `Message` row to serialize.

        Returns:
            dict: Storage-shaped message-row payload.
        """
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

    def _raise_message_runtime_deprecation(self, method_name: str) -> None:
        """Fail when callers try to use message storage as a live history owner.

        Args:
            method_name: Deprecated method name the caller attempted to use.

        Returns:
            Never: This helper always raises a message history persistence error.
        """
        raise MessageHistoryPersistenceError(
            f"MessagesRepository.{method_name} is deprecated for shared message/history access; use MessageRuntime functions instead"
        )

    def list_history(
        self,
        *,
        limit: int | None = None,
        before_sequence_no: int | None = None,
        after_sequence_no: int | None = None,
    ) -> list[dict]:
        """Reject deprecated shared-history access on message persistence.

        Args:
            limit: Optional maximum number of history rows the caller requested.
            before_sequence_no: Optional upper sequence boundary for older rows.
            after_sequence_no: Optional lower sequence boundary for newer rows.

        Returns:
            Never: This method always raises to enforce MessageRuntime-function usage.
        """
        self._raise_message_runtime_deprecation("list_history")

    def get_message_by_sequence_no(self, sequence_no: int) -> dict | None:
        """Reject deprecated shared message lookup on message persistence.

        Args:
            sequence_no: Positive sequence number requested by the caller.

        Returns:
            Never: This method always raises to enforce MessageRuntime-function usage.
        """
        self._raise_message_runtime_deprecation("get_message_by_sequence_no")

    def load_recent_history(
        self,
        *,
        limit: int,
        before_sequence_no: int | None = None,
    ) -> list[dict]:
        """Reject deprecated shared recent-history access on message persistence.

        Args:
            limit: Maximum number of recent rows the caller requested.
            before_sequence_no: Optional sequence boundary to stop before.

        Returns:
            Never: This method always raises to enforce MessageRuntime-function usage.
        """
        self._raise_message_runtime_deprecation("load_recent_history")

    def load_next_sequence_no(self) -> int:
        """Reject deprecated shared next-sequence access on message persistence.

        Args:
            None.

        Returns:
            Never: This method always raises to enforce MessageRuntime-function usage.
        """
        self._raise_message_runtime_deprecation("load_next_sequence_no")

    def store_artifact(self, artifact_data: dict) -> dict:
        """Reject deprecated shared artifact storage on message persistence.

        Args:
            artifact_data: Message-artifact payload requested by the caller.

        Returns:
            Never: This method always raises to enforce MessageRuntime-function usage.
        """
        self._raise_message_runtime_deprecation("store_artifact")

    def list_by_project(
        self,
        *,
        limit: int | None = None,
        before_sequence_no: int | None = None,
        after_sequence_no: int | None = None,
    ) -> list[dict]:
        """Reject deprecated ambiguous list method on message persistence.

        Args:
            limit: Optional maximum number of rows the caller requested.
            before_sequence_no: Optional upper sequence boundary for older rows.
            after_sequence_no: Optional lower sequence boundary for newer rows.

        Returns:
            Never: This method always raises to direct callers to `list_message_rows`.
        """
        self._raise_message_runtime_deprecation("list_by_project")

    def get_by_sequence_no(self, sequence_no: int) -> dict | None:
        """Reject deprecated ambiguous lookup method on message persistence.

        Args:
            sequence_no: Positive sequence number requested by the caller.

        Returns:
            Never: This method always raises to direct callers to `get_message_row_by_sequence_no`.
        """
        self._raise_message_runtime_deprecation("get_by_sequence_no")

    def list_message_rows(
        self,
        *,
        limit: int | None = None,
        before_sequence_no: int | None = None,
        after_sequence_no: int | None = None,
    ) -> list[dict]:
        """List serialized message rows for the configured project.

        Args:
            limit: Optional maximum number of message rows to return.
            before_sequence_no: Optional upper sequence boundary for older rows.
            after_sequence_no: Optional lower sequence boundary for newer rows.

        Returns:
            list[dict]: Ordered serialized message rows for the current project.
        """
        project_id = self._require_project_id()
        if before_sequence_no is not None:
            before_sequence_no = self._validate_sequence_no(before_sequence_no, field_name="before_sequence_no")
        if after_sequence_no is not None:
            after_sequence_no = self._validate_sequence_no(after_sequence_no, field_name="after_sequence_no")

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

    def get_message_row_by_sequence_no(self, sequence_no: int) -> dict | None:
        """Load one serialized message row by ordered sequence number.

        Args:
            sequence_no: Positive sequence number of the message to load.

        Returns:
            dict | None: Serialized message row when found, otherwise `None`.
        """
        project_id = self._require_project_id()
        sequence_no = self._validate_sequence_no(sequence_no, field_name="sequence_no")
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

    def load_recent_message_rows(
        self,
        *,
        limit: int,
        before_sequence_no: int | None = None,
    ) -> list[dict]:
        """Load a bounded recent-history window for the configured project.

        Args:
            limit: Maximum number of recent message rows to load.
            before_sequence_no: Optional sequence boundary to stop before.

        Returns:
            list[dict]: Ordered recent-history rows for the current project.
        """
        project_id = self._require_project_id()
        if limit < 1:
            raise MessageHistoryPersistenceError("limit must be >= 1")
        if before_sequence_no is not None:
            before_sequence_no = self._validate_sequence_no(before_sequence_no, field_name="before_sequence_no")

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
            raise MessageHistoryPersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()

    def load_next_message_sequence_no(self) -> int:
        """Load the next sequence number for a new stored message row.

        Args:
            None.

        Returns:
            int: Next ordered sequence number for the current project.
        """
        project_id = self._require_project_id()
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(func.max(Message.sequence_no)).where(Message.project_id == project_id)
            current_max = session.execute(stmt).scalar_one_or_none()
            return (current_max or 0) + 1
        except SQLAlchemyError as e:
            raise MessageHistoryPersistenceError(str(e)) from e
        finally:
            if self.db_connection is None:
                session.close()

    def insert_message_row(self, message_data: dict) -> dict:
        """Insert one message row into persistence for the configured project.

        Args:
            message_data: Message-row payload to insert, optionally including project id.

        Returns:
            dict: Serialized stored message row after persistence completes.
        """
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

    def store_message_artifact(self, artifact_data: dict) -> dict:
        """Persist one message artifact using the standard insert path.

        Args:
            artifact_data: Message-row payload to store for the current project.

        Returns:
            dict: Serialized stored message row after persistence completes.
        """
        return self.insert_message_row(artifact_data)
