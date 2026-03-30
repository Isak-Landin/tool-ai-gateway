from __future__ import annotations

from errors import MessageHistoryPersistenceError, MessageRuntimeError


class MessageRuntime:
    """
    Project-bound message/history serving surface.

    This runtime object reuses the persistence-facing MessagesRepository for
    project-scoped history retrieval and route/shared message shaping without
    taking over execution-owned context-limit policy or ordered artifact writes.
    """

    def __init__(self, *, project_id: int, messages_repository):
        if project_id is None:
            raise MessageRuntimeError("project_id is required")
        if messages_repository is None:
            raise MessageRuntimeError("messages_repository is required")

        self.project_id = project_id
        self.messages_repository = messages_repository

    def list_history(
        self,
        *,
        limit: int | None = None,
        before_sequence_no: int | None = None,
        after_sequence_no: int | None = None,
    ) -> list[dict]:
        try:
            return self.messages_repository.list_by_project(
                limit=limit,
                before_sequence_no=before_sequence_no,
                after_sequence_no=after_sequence_no,
            )
        except MessageHistoryPersistenceError as e:
            raise MessageRuntimeError(str(e)) from e

    def get_message_by_sequence_no(self, sequence_no: int) -> dict | None:
        try:
            return self.messages_repository.get_by_sequence_no(sequence_no)
        except MessageHistoryPersistenceError as e:
            raise MessageRuntimeError(str(e)) from e
