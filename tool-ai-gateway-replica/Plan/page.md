# Plan

_Current development plan and next targets for tool-ai-gateway._

## Active Focus

Completing the MVP execution loop with ordered persistence and completing the project-entry bootstrap decision surface.

## Sub-pages

- **Plan/MVP** — MVP completion targets and blockers
- **Plan/API** — API route plan and missing route surface
- **Plan/UI** — UI plan and frontend targets
- **Plan/Final-Intent** — Long-term product and architecture intent

## Current Priority Order

1. **MVP execution persistence** — wire ordered message artifact writes (user, assistant, tool) through execution
2. **FileRuntime selected context confirmation** — confirm selected context loading is wired correctly in execution
3. **Project-entry bootstrap decision** — implement the backend-owned project-entry decision surface
4. **Branch enumeration** — add a backend route for available branches
5. **UI bootstrap flow** — connect UI to the new backend project-entry surface

## Blockers

- `ProjectExecutionPersistence` wiring in `workflow_orchestrator.py` — primary execution MVP blocker
- No backend project-entry decision route — blocks consistent bootstrap follow-up behavior

## Next After MVP

- **MCP Tool Integration** — replace hardcoded tool modules with MCP server-based tool delivery; implement MCP client manager, per-server registration persistence, and dynamic tool aggregation
- Repository transport/sync route surface (fetch, pull, push, remote connectivity)
- Activity feed (dedicated backend route beyond message history)
- Auth/account route surface (user accounts, login, profile)
