# Persistence

The `persistence/` package owns all database-backed reads and writes plus persistence-backed file snapshot storage.

## Repositories

| Module | Owns |
|---|---|
| `ProjectPersistence/` | Project row reads and writes (create, get, update, list) |
| `ResolutionPersistence/` | Narrow read surface for project resolution (used by `ProjectResolver`) |
| `RuntimeBindingPersistence/` | Narrow read surface for runtime binding fields (used by `ProjectRuntimeBinder`) |
| `MessagesRepository/` | Project-scoped message row storage: ordered reads, artifact writes, sequence management |
| `FilesRepository/` | Project-scoped file snapshot rows: upsert, get by path, list |
| `BoundProjectRuntimePersistence/` | Wrapper surface used during bound runtime for persistence-backed project state |

## Ownership Rules

- All repositories are storage-shaped — they own rows, not behavior
- `MessagesRepository` is not a shared message/history owner; use `MessageRuntime` functions for that
- `FilesRepository` is not a live file owner; use `FileRuntime` for live file/tree/search reads
- Each repository requires an explicit `db_connection` and `project_id` (where applicable)
- Persistence surfaces should not call upward or orchestrate

## Session Management

DB sessions come from `db/session.py` (`SessionLocal`). Repositories accept an optional `db_connection` passed from the calling route or execution layer, enabling shared session patterns.

## MVP Status

Message persistence is MVP-critical. `MessagesRepository` plus `MessageRuntime` functions cover the required ordered message artifact storage. File snapshot storage via `FilesRepository` + `FileRuntime.persist_file_snapshot(...)` exists but is not yet wired into the live execution path.
