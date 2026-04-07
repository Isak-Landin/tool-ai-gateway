# MessageRuntime

`MessageRuntime/MessageRuntime.py` — function module for project-scoped message operations.

## Purpose

Composes a caller-supplied `MessagesRepository` into route-usable and execution-usable message operations. Owns higher-level message/history behavior and error translation.

Does **not** own: DB session creation, project-id ownership, or message-row persistence internals.

## Public Functions

| Function | Purpose |
|---|---|
| `load_messages(repo, *, limit, before_sequence_no, after_sequence_no)` | Load message rows with optional filters |
| `load_message_by_sequence_no(repo, sequence_no)` | Load one message row by sequence number |
| `load_recent_messages(repo, *, limit, before_sequence_no)` | Load bounded recent message window |
| `load_next_message_sequence_no(repo)` | Get next sequence number for artifact writes |
| `store_message_artifact(repo, artifact_data)` | Persist one message artifact |

## Usage Pattern

All functions take an explicit `messages_repository` as the first argument. The caller supplies the `MessagesRepository(project_id=...)` — the function module does not create or own it.

```python
from MessageRuntime import load_recent_messages, store_message_artifact

messages_repository = MessagesRepository(db_connection, project_id=project_id)
history = load_recent_messages(messages_repository, limit=20)
```

## Ownership

- Execution uses `MessageRuntime` for bounded history loads and ordered artifact writes
- Routes use `MessageRuntime` for message history reads (via a route-owned `MessagesRepository`)
- `MessagesRepository` is the storage layer; `MessageRuntime` is the behavior layer
- `MessagesRepository` now fails explicitly if called like a shared message/history owner

## Error Translation

`MessageHistoryPersistenceError` from the repository is translated to `MessageRuntimeError` at this surface.
