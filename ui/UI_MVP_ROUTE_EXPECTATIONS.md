# UI MVP Route Expectations

_This document maps the must-have MVP UI routes to the backend-backed data they should expect._

_Backend models and lower-layer ownership are the primary anchors. Current UI placeholders are only secondary reference material._

## Scope

Included:

- landing page as MVP entry
- project collection routes
- project workspace routes

Excluded for now:

- auth and account flows
- collaboration/user ownership flows
- final-product-only route expansion

## Backend Data Anchors

The main backend anchors for current UI expectation are:

- `db.models.Project`
- `db.models.Message`
- `ProjectResolver`
- `ProjectRuntimeBinder`
- `BoundProjectRuntime`
- `MessageRuntime`
- `ExecutionPersistence`
- `MessagesRepository`
- `FileRuntime`
- `FilesRepository`
- repository inspection helpers

## Current Backend Data Available

### Project-backed data

Project data currently appears to support:

- `project_id`
- `name`
- `repo_path`
- `remote_repo_url`
- `branch`
- `ssh_key`
- `public_key_path`
- `created_at`
- `updated_at`

Important change:

- `projects.ai_model_name` is deprecated and should not be treated as current truth

### Message-backed data

Message data currently appears to support:

- `id`
- `project_id`
- `sequence_no`
- `role`
- `content`
- `thinking`
- `ai_model_name`
- `tool_name`
- `tool_calls_json`
- `images_json`
- `ollama_created_at`
- `done`
- `done_reason`
- `total_duration`
- `load_duration`
- `prompt_eval_count`
- `prompt_eval_duration`
- `eval_count`
- `eval_duration`
- `raw_message_json`
- `raw_response_json`
- `created_at`

Message ownership expectation:

- execution still uses `ExecutionPersistence` for bounded recent-history loading and ordered artifact writes during runs
- route/shared history reads should move toward a bound project-scoped message surface that reuses `MessagesRepository`

### Repository/file data

Repository/file surfaces currently appear to support:

- tree entries:
  - `name`
  - `path`
  - `is_dir`
  - `is_file`
  - `depth`
- file reads:
  - `name`
  - `path`
  - `content`
  - `start_line`
  - `end_line`
  - `total_lines`
- text search:
  - `path`
  - `line_number`
  - `line_text`

## Must MVP UI Routes

## 1. Landing Page

### UI route

- `/`

### UI route package

- `ui/webapp/routes/public/`

### Backend expectation

Required now:

- none

Optional later:

- health/status summary
- simple project count

## 2. Projects List

### UI route

- `/projects`

### UI route package

- `ui/webapp/routes/projects/`

### Backend route alignment

- `GET /projects`

### Required backend data

Per project:

- `project_id`
- `name`
- `branch`
- `created_at`

### Notes

If the UI wants:

- status badge
- readiness label
- bootstrap label

those are not currently strong backend fields and should be treated as derived or deferred.

The old assumption that the list should display a project-owned selected model is deprecated.

## 3. Create Project

### UI route

- `/projects/new`

### UI route package

- `ui/webapp/routes/projects/`

### Backend route alignment

- `POST /projects`

### Required request data

- `name`
- `remote_repo_url`

### Required response data

- `ok`
- `project_id`
- `name`
- `remote_repo_url`
- `public_key`

## 4. Project Workspace

### UI route

- `/projects/<project_id>`

### UI route package

- `ui/webapp/routes/project/`

### Backend route alignment

This route depends on composed backend data from:

- `GET /projects/{project_id}`
- `GET /projects/{project_id}/messages` expected route
- `GET /projects/{project_id}/repository/tree` expected route
- `GET /projects/{project_id}/repository/file` expected route
- `POST /projects/{project_id}/run`

### Required project shell data

- `project_id`
- `name`
- `branch`
- `created_at`

### Required repository tree data

- `name`
- `path`
- `is_dir`
- `is_file`
- `depth`

### Required file presenter data

- `name`
- `path`
- `content`
- `start_line`
- `end_line`
- `total_lines`

### Required chat/history data

- `id`
- `sequence_no`
- `role`
- `content`
- `thinking`
- `ai_model_name`
- `tool_name`
- `tool_calls_json`
- `created_at`

### Required run submission data

The workspace should send:

- `message`
- `selected_files`
- optional `branch`
- optional `ai_model_name`

The workspace should expect back at minimum:

- `ok`
- `project_id`
- `message`
- `selected_files`
- `branch`
- `ai_model_name`

### Model selection expectation

The workspace visually expects model selection, but that selection is no longer project metadata.

Current intended behavior:

- the model dropdown is a workspace/run-time control
- the chosen value is sent with a run when needed
- the message history archives the actual `ai_model_name` used

For MVP simplicity right now:

- the UI may provide a static model-option list locally

Longer-term intended direction:

- a separate non-persistence-backed backend route such as `/models`

That route is documented direction only, not a current implementation requirement.

### Current backend sufficiency

Enough to support the workspace direction:

- mostly yes

Primary gap:

- dedicated API exposure for history, repository tree, and repository file reads

## 5. Project Settings

### UI route

- `/projects/<project_id>/settings`

### UI route package

- `ui/webapp/routes/project/`

### Backend route alignment

- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}` expected route

### Required backend data

- `project_id`
- `name`
- `branch`
- `created_at`

### Reasonable mutable project fields

- `name`
- `branch`

### Not intended as project settings

- persistent selected model

That older assumption is deprecated.

## 6. Project Activity

### UI route

- `/projects/<project_id>/activity`

### UI route package

- `ui/webapp/routes/project/`

### Backend route alignment

- `GET /projects/{project_id}/messages` expected route

### Required backend data

- `sequence_no`
- `role`
- `content`
- `thinking`
- `ai_model_name`
- `tool_name`
- `created_at`

Useful if exposed:

- `done_reason`
- `tool_calls_json`
- duration fields

## Route Package Placement Summary

### `ui/webapp/routes/public/`

Must MVP route:

- `/`

### `ui/webapp/routes/projects/`

Must MVP routes:

- `/projects`
- `/projects/new`

### `ui/webapp/routes/project/`

Must MVP routes:

- `/projects/<project_id>`
- `/projects/<project_id>/settings`

Reasonable MVP route:

- `/projects/<project_id>/activity`

## Real Gaps vs Deprecated Assumptions

### Real gaps

- dedicated message-history API route
- dedicated repository tree API route
- dedicated repository file-read API route
- explicit branch-option sourcing if the UI needs a real dropdown

### Deprecated assumptions

- project owns current selected model
- project list must show backend-backed model field
- project settings should edit a project-owned selected model

## Bottom Line

The backend models and lower layers already support the core MVP UI direction.

The important correction is:

- model choice is not project-owned
- message artifacts archive the actual `ai_model_name` used
- model-option sourcing may stay static in the UI for MVP
- a future separate live model-availability route can exist later without being persistence-backed
