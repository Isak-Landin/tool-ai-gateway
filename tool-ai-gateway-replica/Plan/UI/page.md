# Plan — UI

_UI plan and frontend targets._

## Immediate Targets

### Bootstrap flow completion

Once the backend project-entry decision route exists:

- Connect `/projects/<project_id>` entry to the backend decision surface
- Show bootstrap guidance when `bs2_pending`
- Show workspace when `ready`
- Remove any client-side bootstrap logic from UI routes

### Branch selector

Once `GET /projects/{project_id}/repository/branches` exists:

- Replace freeform branch text input with a real branch dropdown
- Pre-populate from the backend branch list
- Show active branch as selected

### Chat run state feedback

- Show loading/in-progress state while a run is executing
- Display tool call activity during execution (tool name, result summary)
- Show model name used for each assistant response

## Post-MVP UI Targets

### Activity feed

Once the backend activity route exists:

- Replace message-history-only activity display with a real activity timeline
- Show execution events, tool call metadata, bootstrap milestones

### Repository sync controls

Once backend transport routes exist:

- Add fetch/pull controls in the workspace or settings
- Show last-synced status and remote connectivity state

### Model selector

- Connect to a backend model list (once exposed)
- Allow per-run model override from the workspace
- Show active model in workspace header

### Auth and account pages

When user accounts are implemented:

- Wire `/login`, `/register`, `/logout` to backend auth routes
- Wire `/account/*` profile/preferences/security pages to backend account routes
- Remove placeholder-only forms

## Current Issues

See `UI/UI bugs` for active bugs and frontend/backend mismatches.
