# Plan — API

_API route surface plan and missing route targets._

## Current Live Surface

All live routes are scoped to `/projects`. See `Skeleton/API` for the full current list.

## Immediate MVP Route Targets

### Project-entry decision (blocking)

```
GET /projects/{project_id}/entry
```
Returns: `{status: "bootstrap_pending" | "bs2_pending" | "ready", ...}`

Backend-owned. UI must follow this decision for project page entry.

### Branch enumeration (blocking for UI branch selector)

```
GET /projects/{project_id}/repository/branches
```
Returns: `{branches: ["main", "dev", ...], active_branch: "main"}`

Served via `RepositoryRuntime` git branch listing.

## Post-MVP Route Targets

### Repository transport / sync

```
POST /projects/{project_id}/repository/fetch
POST /projects/{project_id}/repository/pull
GET  /projects/{project_id}/repository/sync-status
```

These must be added in coordination with UI sync controls. Ownership stays lower-layer/runtime-owned through `RepositoryRuntime` — not bypassed from routes directly.

### Activity feed

```
GET /projects/{project_id}/activity
```

A dedicated activity/timeline route beyond message history. Returns project events (messages, tool calls, repository milestones, bootstrap milestones) as an ordered activity stream.

### Auth / Account (later intent)

```
POST /auth/login
POST /auth/register
POST /auth/logout
GET/PATCH /account/profile
GET/PATCH /account/preferences
```

User accounts are later-intent, not current MVP scope.

## Ownership Rules for New Routes

- New routes must delegate to the appropriate internal layer (Execution, Persistence) via the existing chain
- Routes do not own execution logic, persistence internals, or business logic
- Route-facing live file reads go through `FileRuntime`; message history through `MessageRuntime` functions
- Branch listing must go through `RepositoryRuntime` — not invented on the route level
