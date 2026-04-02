"""
Internal rules for message-runtime function helpers.

Ownership:
- This file owns higher-level message/history behavior that composes a caller-
  supplied `MessagesRepository` into route-usable and execution-usable message
  operations.
- This file owns message-specific validation and message-runtime-shaped error
  translation.
- This file does not own DB-session creation, project-id ownership, or message
  row persistence internals.

Rule-set split:
- Internal helper rules apply to shared validation and dependency/error
  translation helpers used by message operations.
- Encapsulated/public helper rules apply to exposed message use-case functions.

Internal helper rules:
- Public message functions must validate caller-supplied runtime inputs before
  delegating to persistence.
- Public message functions must require an explicit `messages_repository`
  dependency through `_require_messages_repository(...)`.
- Persistence failures must be translated from `MessageHistoryPersistenceError`
  into `MessageRuntimeError`.

Encapsulated/public helper rules:
- Read-oriented helpers should keep caller policy explicit through parameters
  such as `limit`, `before_sequence_no`, and `after_sequence_no` instead of
  hiding those decisions inside this file.
- `load_messages(...)`, `load_message_by_sequence_no(...)`,
  `load_recent_messages(...)`, `load_next_message_sequence_no(...)`, and
  `store_message_artifact(...)` are the message-runtime use-case surface and
  should compose only the declared internal helper rules plus the storage-shaped
  repository methods they target.
"""

from __future__ import annotations

from errors import MessageHistoryPersistenceError, MessageRuntimeError


def _require_messages_repository(messages_repository):
    if messages_repository is None:
        raise MessageRuntimeError("messages_repository is required")

    return messages_repository


def _validate_sequence_no(sequence_no: int, *, field_name: str) -> int:
    if sequence_no < 1:
        raise MessageRuntimeError(f"{field_name} must be >= 1")

    return sequence_no


def load_messages(
    messages_repository,
    *,
    limit: int | None = None,
    before_sequence_no: int | None = None,
    after_sequence_no: int | None = None,
) -> list[dict]:
    if before_sequence_no is not None:
        before_sequence_no = _validate_sequence_no(
            before_sequence_no,
            field_name="before_sequence_no",
        )
    if after_sequence_no is not None:
        after_sequence_no = _validate_sequence_no(
            after_sequence_no,
            field_name="after_sequence_no",
        )

    required_messages_repository = _require_messages_repository(messages_repository)
    try:
        return required_messages_repository.list_message_rows(
            limit=limit,
            before_sequence_no=before_sequence_no,
            after_sequence_no=after_sequence_no,
        )
    except MessageHistoryPersistenceError as e:
        raise MessageRuntimeError(str(e)) from e


def load_message_by_sequence_no(messages_repository, sequence_no: int) -> dict | None:
    normalized_sequence_no = _validate_sequence_no(sequence_no, field_name="sequence_no")
    required_messages_repository = _require_messages_repository(messages_repository)
    try:
        return required_messages_repository.get_message_row_by_sequence_no(normalized_sequence_no)
    except MessageHistoryPersistenceError as e:
        raise MessageRuntimeError(str(e)) from e


def load_recent_messages(
    messages_repository,
    *,
    limit: int,
    before_sequence_no: int | None = None,
) -> list[dict]:
    if before_sequence_no is not None:
        before_sequence_no = _validate_sequence_no(
            before_sequence_no,
            field_name="before_sequence_no",
        )

    required_messages_repository = _require_messages_repository(messages_repository)
    try:
        return required_messages_repository.load_recent_message_rows(
            limit=limit,
            before_sequence_no=before_sequence_no,
        )
    except MessageHistoryPersistenceError as e:
        raise MessageRuntimeError(str(e)) from e


def load_next_message_sequence_no(messages_repository) -> int:
    required_messages_repository = _require_messages_repository(messages_repository)
    try:
        return required_messages_repository.load_next_message_sequence_no()
    except MessageHistoryPersistenceError as e:
        raise MessageRuntimeError(str(e)) from e


def store_message_artifact(messages_repository, artifact_data: dict) -> dict:
    required_messages_repository = _require_messages_repository(messages_repository)
    try:
        return required_messages_repository.store_message_artifact(artifact_data)
    except MessageHistoryPersistenceError as e:
        raise MessageRuntimeError(str(e)) from e
