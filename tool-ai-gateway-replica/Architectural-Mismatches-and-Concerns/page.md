# Architectural Mismatches and Concerns

_Gap and deprecation register. Source of truth: `ARCHITECTURAL_MISMATCHES_AND_CONCERNS.md`_

_Tracks what is still wrong, missing, deprecated, or architecturally risky for MVP alignment. Solved items should be removed unless they still create an active deprecation risk._

---

## MVP-Critical Active Gaps

### 1. Project-entry bootstrap follow-up behavior is not implemented

After `POST /projects` succeeds, the UI should route to `/projects/{project_id}` and the backend should own the decision: continue to workspace, show bootstrap page, or run BS2.

**Current state:** No stable backend route or persistence contract for this decision exists.

**Risk:** UI can harden around the wrong assumption (separate continuation page). Users lose consistent bootstrap follow-up on refresh or deep-link.

---

### 2. Branch-aware workspace lacks authoritative branch-source support

Routes support branch-aware reads and runs, but no backend route lists valid repository branches.

**Current state:** Branch input is freeform. Invalid branch values fail late during route binding or repository access.

**Risk:** Future UI work can silently invent fake branch options. Branch UX drifts into client-side guessing.

---

### 3. Project activity is backed only by message history

`/projects/<project_id>/activity` routes to `GET /projects/{project_id}/messages`. No dedicated activity/timeline route for richer project events exists.

**Risk:** Future UI activity work reshapes message rows into a pseudo-activity model on the client. Project history ownership can drift.

---

### 4. Repository transport/sync expectations are missing from the backend

No backend routes for: branch enumeration, git fetch/pull/push, clone/sync status, remote connectivity verification after bootstrap.

**Risk:** Future UI sync controls have no backend surface. Bootstrap can appear complete even when the repo is not remotely usable.

---

## Later-Intent User-Account-Dependent Gaps

These gaps depend on user-account existence, which is expected for final/later MVP intent, not for the current project-scoped backend pass.

### 5. UI route surface exceeds the live FastAPI backend for auth/account/settings

Live FastAPI only exposes project-scoped routes. Flask UI exposes: `/login`, `/register`, `/forgot-password`, `/reset-password`, `/accept-access`, `/logout`, `/account/*`, `/settings`.

No backend contracts exist for these.

**Risk:** Future UI work can harden around nonexistent backend contracts. Browser-only states are invented where the backend has no ownership.

### 6. User/account/application settings routes remain UI-only shells

Profile, preferences, security, and application-level settings pages exist as stable-looking product routes with no backend ownership plan.

**Risk:** Future work retrofits inconsistent backend contracts under visually established route shells.
