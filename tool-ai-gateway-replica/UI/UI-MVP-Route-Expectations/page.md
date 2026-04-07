# UI MVP Route Expectations

_What each live UI route expects from the FastAPI backend._

## `/projects` — Project List

**Owner:** `ui/webapp/routes/projects/`

**Expects:**
- `GET /projects` → list of project objects `[{project_id, name, remote_repo_url, branch}]`
- `POST /projects` → create project, returns `{project_id, name, remote_repo_url, public_key}`

**After POST:** UI routes to `/projects/<project_id>`. Backend must provide a stable decision on whether bootstrap or workspace should be shown.

---

## `/projects/<project_id>` — Workspace

**Owner:** `ui/webapp/routes/project/`

**Expects:**
- `GET /projects/{project_id}` → project details + active branch
- `GET /projects/{project_id}/repository/tree` → branch-aware file tree
- `GET /projects/{project_id}/repository/file` → file content from branch
- `GET /projects/{project_id}/repository/search` → text search in branch
- `POST /projects/{project_id}/run` → execute chat run, returns assistant response

**Live owners:**
- File tree, file read, search → `FileRuntime`
- Chat history → `MessageRuntime` functions
- Run execution → `execution/workflow_orchestrator.py`

---

## `/projects/<project_id>/activity` — Activity

**Owner:** `ui/webapp/routes/project/` (activity sub-route)

**Expects:**
- `GET /projects/{project_id}/messages` → ordered message history

**Gap:** No dedicated activity/timeline route. Only message history available. Richer activity feed is a future backend concern.

---

## `/projects/<project_id>/settings` — Settings

**Owner:** `ui/webapp/routes/project/` (settings sub-route)

**Expects:**
- `GET /projects/{project_id}` → current settings (branch, remote URL, name)
- `PATCH /projects/{project_id}` → update settings

**Gap:** No branch validation against an authoritative branch list — branch input is currently freeform.

---

## Missing Route Dependencies

| UI Page | Expected Backend Route | Status |
|---|---|---|
| Branch selector | `GET /projects/{id}/repository/branches` | Missing |
| Repository sync | `POST /projects/{id}/repository/sync` | Missing |
| Bootstrap decision | `GET /projects/{id}/entry` | Missing |
| Auth pages | `/auth/*` | Missing |
| Account pages | `/account/*` | Missing |
