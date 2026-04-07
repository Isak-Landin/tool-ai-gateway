# UI Bugs and Current Issues

_Active UI issues and known frontend/backend mismatches._

## Bootstrap Step 2 — Mapping Issues

When a project is created and the UI routes to `/projects/<project_id>`:

- The backend does not yet expose a stable decision surface for whether to show the bootstrap guidance page or the workspace
- The UI cannot currently distinguish "BS1 done, BS2 pending" from "BS2 done, ready for workspace" without backend-owned bootstrap follow-up behavior
- Page refresh or deep-link to `/projects/<project_id>` cannot rely on a settled backend contract

## Branch Selector

- Branch selection is currently freeform text input — not a dropdown backed by an authoritative branch list
- Invalid branch values fail late (at tree/file/search/run time) rather than being caught earlier
- Backend branch enumeration route is missing

## Activity Page

- Activity at `/projects/<project_id>/activity` shows only message history
- No first-class activity/timeline feed
- Tool-call metadata (tool name, duration) is stored in message fields but not surfaced distinctly

## Auth / Account Pages

- `/login`, `/register`, `/forgot-password`, and account pages render as complete-looking product surfaces
- No backend API contracts exist for these routes
- Forms and buttons on these pages have no backend handling
- Risk: future work may harden around nonexistent backend contracts

## Repository Sync Controls

- No UI controls exist yet for fetch, pull, push, or remote connectivity check
- Backend route surface for repository transport/sync is also missing
- These must be added in coordination once the backend route surface is defined

## Model Selector

- Model selector may not reflect the actual available models from the Ollama instance
- Model names are currently configured statically rather than discovered from the backend
