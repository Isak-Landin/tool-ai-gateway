# API

The `api_routes/` package owns all FastAPI route definitions.

## Current Route Surface

All live routes are scoped under `/projects`.

### project_routes

Located in `api_routes/project_routes/`:

- `router.py` — FastAPI router with all project-scoped endpoints
- `runtime.py` — Route-level runtime helper (project resolution + binding)
- `schemas.py` — Request/response Pydantic schemas

Current endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/projects` | List all projects |
| `POST` | `/projects` | Create new project (triggers BS1) |
| `GET` | `/projects/{project_id}` | Get project details + branch |
| `PATCH` | `/projects/{project_id}` | Update project settings |
| `GET` | `/projects/{project_id}/messages` | Get ordered message history |
| `GET` | `/projects/{project_id}/repository/tree` | Live branch-aware file tree |
| `GET` | `/projects/{project_id}/repository/file` | Read file from branch |
| `GET` | `/projects/{project_id}/repository/search` | Search text in branch |
| `POST` | `/projects/{project_id}/run` | Execute a chat run |

### model_routes

Located in `api_routes/model_routes/`:

- Exposes model/LLM configuration endpoints

## Ownership

- Routes own input validation, project resolution call, runtime binding, and execution delegation
- Routes do not own execution logic, persistence internals, or response business logic
- Route-facing live file reads go through `FileRuntime`; message history through `MessageRuntime` functions

## Missing Backend Surface (Active Gaps)

The following route categories are currently missing from the live backend:

- Branch enumeration / validation
- Repository transport/sync (fetch, pull, push, clone status)
- Project bootstrap follow-up decision surface
- Activity / timeline feed beyond message history
- Auth / account / user profile routes

See `Plan/API` for planned route additions and `Architectural Mismatches and Concerns` for gap details.
