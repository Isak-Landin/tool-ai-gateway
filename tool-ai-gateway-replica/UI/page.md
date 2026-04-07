# UI

The `ui/` package owns the Flask-based web interface for the tool-ai-gateway.

## Structure

```
ui/
├── app.py               — Flask application factory
├── webapp/
│   ├── gateway_api.py   — API client for FastAPI backend calls
│   ├── navigation.py    — Navigation helpers
│   ├── formatting.py    — Template formatting helpers
│   ├── config.py        — UI config
│   ├── trusted_hosts.py — Trusted host middleware
│   └── routes/
│       ├── account/     — Account/profile routes (UI-only shells)
│       ├── app_pages/   — Application settings (UI-only shell)
│       ├── project/     — Single project workspace routes
│       ├── projects/    — Project list routes
│       ├── public/      — Public/auth pages (login, register, etc.)
│       ├── support/     — Support pages
│       └── ui_api/      — UI-internal API helpers
```

## Live Route Surface

Active routes backed by real API behavior:

- `/projects` — project list
- `/projects/<project_id>` — project workspace (chat, file tree, run)
- `/projects/<project_id>/activity` — message history (via messages API)
- `/projects/<project_id>/settings` — project settings (branch, remote URL)

## UI-Only Shell Routes (No Backend Contract)

The following routes exist in UI but have no matching FastAPI backend:

- `/login`, `/register`, `/forgot-password`, `/reset-password`
- `/account`, `/account/profile`, `/account/preferences`, `/account/security`
- `/settings` (application settings)

These are documented gaps. See `Architectural Mismatches and Concerns`.

## Sub-pages

- **UI Intent Map** — full UI direction and final intent
- **UI MVP Route Expectations** — what each route expects from the backend
- **UI bugs** — current UI issues
