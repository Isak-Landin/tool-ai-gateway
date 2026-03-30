# Architectural Mismatches and Concerns

_This document is a gap/deprecation register._

_It exists to track what is still wrong, missing, deprecated, or architecturally risky for MVP alignment._

_It is **not** a map of implemented features, and it should not retain solved items except where a solved item still creates an active deprecation risk above it._

## Purpose

Use this file to keep three things explicit:

- unresolved architectural gaps
- active deprecations that still matter
- missing functionality or missing adoption that still blocks clean MVP behavior

## Source-of-Truth Rule

For this file:

- documented intended ownership remains the source of truth
- current code is only evidence of remaining gaps or drift
- once a gap is actually implemented and no longer creates an active blocker, it should be removed from this file

## MVP-Critical Active Gaps and Deprecations

### 1. UI route surface still exceeds the live FastAPI backend surface

The current FastAPI backend only exposes project-scoped routes under `/projects`.

The Flask UI route packages still expose public/account/application pages that visually imply backend-backed actions, but there are no matching backend APIs yet for:

- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`
- `/accept-access`
- `/logout`
- `/account`
- `/account/profile`
- `/account/preferences`
- `/account/security`
- `/settings`

Route issues:

- the public auth pages render forms and action buttons, but there is no backend login/session route contract behind them
- the account pages render as navigable product surfaces, but there is no backend profile/preferences/security route contract behind them
- the application settings page exists as a route shell, but there is no backend settings contract behind it
- invitation/access acceptance has a UI page, but there is no backend invitation-token validation or acceptance route

Current MVP risk:

- future UI work can accidentally harden around nonexistent auth/account/backend contracts
- browser-only success/error states can be invented where the backend has no ownership yet
- route/package structure can look more complete than the backend actually is, which hides real product incompleteness

### 2. Project bootstrap follow-up data is only available at create time

`POST /projects` returns the bootstrap-facing values the UI needs:

- `project_id`
- `name`
- `remote_repo_url`
- `public_key`

But there is no follow-up backend route that lets the UI re-read bootstrap/setup state later.

Route issues:

- `/projects/bootstrap-complete` only works if the browser still has the recent create response in transient state
- a refresh, deep-link, or later revisit cannot re-load the generated `public_key` from the backend
- there is no backend bootstrap-status route that tells the UI whether deploy-key setup is still pending, completed, or invalid

Non-route issues:

- bootstrap state is not yet modeled as a stable route-facing backend resource
- the deploy/public key is operational setup data, but there is no explicit backend-owned reread surface for it

Current MVP risk:

- users can lose bootstrap guidance as soon as the initial create response is gone
- future UI work can be tempted to persist bootstrap-only values in the browser because the backend cannot re-serve them
- bootstrap/setup recovery flows remain undefined even though project creation itself succeeds

### 3. Branch-aware workspace behavior still lacks authoritative branch-source support

The backend supports branch-aware reads and runs through:

- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `GET /projects/{project_id}/repository/tree`
- `GET /projects/{project_id}/repository/file`
- `GET /projects/{project_id}/repository/search`
- `POST /projects/{project_id}/run`

Those routes accept or return one branch value, but there is no backend route that lists valid repository branches or gives the UI an authoritative source for branch selection.

Route issues:

- the workspace can only offer a freeform branch input, not a real branch dropdown
- the settings page can only edit the stored branch string, not validate it against an authoritative branch list
- the workspace cannot ask the backend for “available branches for this repository” before attempting tree/file/search/run work

Current MVP risk:

- invalid branch values fail late during route binding or repository access instead of being prevented earlier
- future UI work can silently invent fake branch options if the missing backend source is not kept explicit
- branch UX can drift into client-side guessing instead of backend-owned repository truth

### 4. Project activity is backed only by message history, not a first-class activity feed

The UI has a dedicated activity route:

- `/projects/<project_id>/activity`

The backend currently supports that route only through:

- `GET /projects/{project_id}/messages`

That is enough for ordered chat/history reading, but there is still no dedicated backend activity/timeline route for richer project events.

Route issues:

- the activity page can only replay message rows, not a first-class project activity stream
- there is no backend route for non-message execution events, repository milestones, or bootstrap milestones as ordered activity records
- tool-call metadata and duration values exist only as message-shaped fields, not as a stable route-facing activity object

Current MVP risk:

- future UI activity work can start reshaping message rows into a pseudo-activity model on the client
- project history ownership can drift if callers start duplicating activity shaping outside the intended bound message surface
- richer activity screens will be tempted to overfit to raw message storage instead of waiting for a true route-facing activity contract

### 5. Repository transport/sync expectations are still missing from the backend route surface

The current backend supports live repository reading/searching plus project-scoped run execution, but it does not expose standalone backend routes for repository transport/sync operations such as:

- git branch enumeration
- git fetch
- git pull
- git push
- git clone/sync status as a route-facing operation
- remote connectivity verification after bootstrap

Route issues:

- any future UI control for “sync repository”, “pull latest”, “push changes”, “check remote”, or “show branch options” would currently have no backend route to call
- project bootstrap currently creates storage plus SSH key material, but there is no route that verifies remote connectivity or reports sync readiness afterward
- repository ownership is intentionally lower-layer/runtime-owned, so adding these later must still preserve the shell/file/message ownership boundaries rather than bypassing them from routes

Current MVP risk:

- future UI work can invent sync/readiness states that are not backend-owned
- git pull/push controls can be reintroduced carelessly through the wrong lower owner if the missing route contract is not documented now
- bootstrap can appear “complete” in UI terms even when the repo is not yet remotely usable

## Active Backend-Support Gaps Outside Current Project MVP

These do not block the current JS-driven project workspace shell, but they are still real route/backend expectation gaps visible in the UI surface.

### 6. Model-option sourcing remains UI-local rather than backend-owned

The backend accepts `ai_model_name` on `POST /projects/{project_id}/run` and archives the actual model on message history, but there is still no backend route for authoritative model-option discovery such as `/models`.

Current risk:

- UI model-option lists can drift from runtime reality
- future UI work can mistake a local convenience list for backend truth

### 7. User/account/application settings routes remain UI-only shells

Even if they are not part of the current workspace MVP, the UI still contains route packages and templates that imply future backend support for:

- user profile reads/updates
- user preference reads/updates
- security/password/session management
- application-level user settings

Current risk:

- these pages can continue to exist as stable-looking product routes without any explicit backend ownership plan
- future work can retrofit inconsistent backend contracts under visually established route shells

## Bottom Line

What remains here should be read as:

- unresolved gap
- active deprecation
- missing route/backend convergence

What has already been implemented should be removed from this file unless it still creates an active unresolved risk above it.
