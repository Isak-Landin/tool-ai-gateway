# Plan — MVP

_MVP completion targets and current blockers._

## Goal

A reliable, ordered, project-scoped chat run that:
- loads bounded recent message context
- loads selected file context via `FileRuntime`
- persists user, assistant, and tool artifacts in correct order via `MessageRuntime`
- uses one execution model per run
- ends when model calls `return_to_user`

## Current Status

The runtime chain is implemented:
- ProjectResolver → ProjectRuntimeBinder → BoundProjectRuntime → Execution → Persistence

`MessageRuntime` functions and `MessagesRepository` exist and are complete. `FileRuntime` for live reads is complete.

## Remaining MVP Work

### 1. Execution Ordered Persistence (Primary Blocker)

`workflow_orchestrator.py` must wire the following in order:

1. Load next message sequence number
2. Persist user turn before model call
3. If tool calls returned: persist assistant tool-call turn, execute tools, persist tool results
4. Continue until `return_to_user`
5. Persist final assistant turn

All via `MessageRuntime.store_message_artifact(messages_repository, artifact_data)`.

### 2. FileRuntime Selected Context Wiring

Confirm that `workflow_orchestrator.py` loads selected context via:
```python
FileRuntime.read_file(repository_runtime, branch=..., relative_repo_path=...)
```
Not via legacy persistence reads.

### 3. Project-Entry Bootstrap Decision Surface

- Implement the backend-owned decision: continue to workspace / show bootstrap guidance / run BS2
- This is a route-level concern in `api_routes/project_routes/router.py`
- Persistence side needs to store and return the bootstrap completion state

### 4. Branch Enumeration Route

- Add `GET /projects/{project_id}/repository/branches`
- Returns available branches from the live repository via `RepositoryRuntime`
- Required for the UI branch selector

## MVP Acceptance Criteria

- A chat run from the UI completes end-to-end
- User, assistant, and tool message artifacts are persisted in sequence
- Message history loads correctly in the UI
- Selected files context is loaded from live branch state
