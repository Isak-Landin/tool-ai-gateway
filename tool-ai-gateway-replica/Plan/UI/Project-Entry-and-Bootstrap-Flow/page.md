# Project Entry and Bootstrap Flow

_Effective route behavior for project creation and project-specific page entry. This is an established intent map, not a description of existing code._

---

## Create Project

**Route:** `POST /projects` (via `GET /projects/new` form)

The create project flow is intentionally short. Its only bootstrap responsibility is triggering BS1 via the backend.

1. User submits name and remote repository URL
2. Backend creates the project row and runs BS1
3. Response returns the generated public SSH key alongside `project_id`
4. UI surfaces the public key to the user
5. UI routes to `/projects/<project_id>`

**Create project never routes to a bootstrap page directly.** All decisions about whether BS1 or BS2 are complete happen at the project-specific page. The create route owns only the form and the POST — the project-specific route owns everything that follows.

---

## Project-Specific Page

**Route:** `GET /projects/<project_id>`

This is the single entry point for both post-creation visits and all later direct visits. There is no separate post-creation route — the same route handles every case.

On every entry, the backend determines whether the project is ready for workspace use. The UI follows that decision.

### Effective decision flow

**BS1 verification fails:**
- If the project is newly created and the project row exists, the backend automatically retries BS1 once
- Retry succeeds → continue to BS2 check
- Retry fails → return an error to the user. No further follow-up for MVP.

**BS2 verification fails:**
- The most likely cause is that the user has not yet added the generated SSH key to their Git host
- This applies equally on the first visit after creation and on any later visit before the key has been added
- The backend surfaces `bootstrap.html` with the public key and instructions
- The user adds the key to their Git host and clicks continue
- Continue routes back to `/projects/<project_id>`, which runs verification again

**Both BS1 and BS2 verification pass:**
- Workspace is shown

### Ownership notes

- This route does not perform bootstrap checks itself
- The backend-owned project-entry decision surface (not yet implemented) sits between this route and `ProjectPersistence` and owns the decision logic above
- `ProjectPersistence` is the only layer that directly calls `bs1(...)`, `bs2(...)`, and verification — the route follows the result, it does not drive it
