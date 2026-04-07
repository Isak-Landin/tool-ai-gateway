# UI Intent Map

_Full intended UI direction and final product shape._

## Workspace

The core product surface is the project workspace at `/projects/<project_id>`.

### Workspace Components

- **Chat panel** — send messages, view ordered message history, see model responses
- **File tree panel** — branch-aware file tree for the active repository
- **File viewer** — view selected file content from the active branch
- **Branch selector** — switch between available branches (requires backend branch list)
- **Model selector** — choose the active model for the run
- **Run control** — trigger a chat run, see execution state

### Navigation

- **Project list** `/projects` — list of all projects, create new project
- **Project workspace** `/projects/<project_id>` — per-project working area
- **Project activity** `/projects/<project_id>/activity` — execution history / activity feed
- **Project settings** `/projects/<project_id>/settings` — edit branch, remote URL, project name

## Model Selection

- UI should expose model selection at workspace level
- Selected model is passed as `ai_model_name` override in the run request
- Default model comes from backend config if not overridden

## Branch Selection

- UI should show an authoritative branch list from the backend (not freeform input)
- Currently missing — backend has no branch enumeration route
- Active gap tracked in Architectural Mismatches

## Bootstrap / Project Entry

- After project creation, UI routes to `/projects/<project_id>`
- Backend decision surface determines: show bootstrap guidance, run BS2, or continue to workspace
- UI must follow backend decision — must not perform bootstrap checks itself
- Bootstrap flow not yet fully implemented on backend side

## Future Intent

- User accounts and auth (login, register, profile, security)
- Application-level settings
- Activity feed with richer project event timeline (beyond message history)
- Invitation / access control
- Repository sync controls (fetch, pull, push, remote status)

## Tech Stack

- Flask (Python) — server-side rendered templates
- Jinja2 templates — HTML rendering
- Static assets in `ui/static/`
