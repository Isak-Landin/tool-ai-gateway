# MVP

_Current MVP execution scope and status._

## Current State

The project-scoped execution layer is the primary active focus. The core runtime chain (ProjectResolver → ProjectRuntimeBinder → BoundProjectRuntime → Execution → Persistence) is implemented.

## What Is Working

- Project resolution and runtime binding are complete
- `BoundProjectRuntime` holder with `RepositoryRuntime` attachment is complete
- `MessageRuntime` function surface for bounded history, sequence management, and artifact writes is complete
- `FileRuntime` for live branch-aware file reads and text search is complete
- `MessagesRepository` and `FilesRepository` persistence surfaces are implemented
- `workflow_orchestrator.py` execution flow exists with model call and tool execution

## What Is Missing / In Progress

### ProjectExecutionPersistence (primary blocker)

The execution layer does not yet have a dedicated persistence surface for the full execution run:

- User turn persistence before model call
- Ordered artifact writes (assistant + tool turns) during the run
- Final assistant turn persistence after the run

The `MessagesRepository` storage surface and `MessageRuntime` functions exist, but the execution-layer wiring to call them in the correct ordered sequence needs to be completed and verified.

### FileRuntime selected context wiring

Execution declares that selected context must come from a bound `FileRuntime` surface, not from self-managed persistence reads. The wiring of `FileRuntime.read_file` for selected context loading in the actual execution run needs to be confirmed as complete.

### Project-entry bootstrap follow-up

The backend-owned decision surface for project-entry (continue vs. bootstrap) is not yet implemented. This blocks consistent bootstrap follow-up on page refresh or deep-link.

### Missing route surface (non-blocking for core MVP)

- Branch enumeration
- Repository transport/sync routes
- Auth/account/application settings routes

## MVP Goal

A reliable, ordered, project-scoped chat run with:

- bounded recent message context
- selected file context from `FileRuntime`
- ordered artifact persistence (user, assistant, tool) via `MessageRuntime`
- one execution model per run
- run ends on `return_to_user`
