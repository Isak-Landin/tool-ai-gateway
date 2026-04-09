# Bootstrap Caller Conclusions

_Established ownership rules for which layers call bootstrap and from where. This page captures concluded behavior, not a description of existing code._

---

## Established Caller Ownership

### ProjectPersistence — sole direct bootstrap caller

`ProjectPersistence` is the only layer permitted to call `bs1(...)`, `bs2(...)`, and bootstrap verification directly. No other layer in the chain — not `ProjectResolver`, `ProjectRuntimeBinder`, `BoundProjectRuntime`, `Execution`, or `RuntimeBindingPersistence` — has caller rights to any bootstrap surface.

**For BS1 (project creation flow):**

- Creates the project row before calling `bs1(...)`
- Derives authoritative bootstrap inputs (project paths, shell)
- Calls `bs1(...)`
- Stores BS1-derived values on the project row: `repo_path`, `ssh_key`, `public_key_path`
- Owns commit/rollback around the mutation

**For BS2 (project-entry flow):**

- Decides when `bs2(...)` should be called
- Passes authoritative inputs including `remote_repo_url` as project metadata
- Owns commit/rollback around any BS2-triggered project-row mutation
- Does not push DB ownership down into `bs2(...)`

**For bootstrap verification:**

- Decides when verification should run
- Passes authoritative project-scoped bootstrap inputs
- Receives the first failure identifier from verification
- Decides what follow-up behavior should occur

---

## Project-Entry Decision Surface

A not-yet-named surface sits between the route and `ProjectPersistence` at the project-specific page entry point. It is the backend-owned decision layer the route follows.

**Owns:**

- Deciding whether normal project-page flow may continue
- Deciding whether bootstrap UI must be shown again
- Deciding whether BS2 should run now
- Acting as the backend-side decision surface the UI route obeys

**Does not own:**

- Bootstrap implementation
- Project-row writes
- Bootstrap helper execution
- UI-route-local logic

This surface is not yet implemented. Its ownership boundaries are established here so implementation does not absorb responsibilities that belong to `ProjectPersistence` or to the route layer.

---

## Layers That Do Not Call Bootstrap

| Layer | Bootstrap Access |
|---|---|
| `ProjectResolver` | None |
| `ProjectRuntimeBinder` | None |
| `BoundProjectRuntime` | None |
| `Execution` | None |
| `RuntimeBindingPersistence` | None |

These layers are downstream consumers of the state that bootstrap produces — `repo_path`, `ssh_key`, `public_key_path` — not participants in the bootstrap process itself.

---

## Bootstrap Verification — No Layer Ownership

`verify_bs_all(...)`, `_verify_bs1(...)`, and `_verify_bs2(...)` are reporting utilities. They are not owned by any named architecture layer. `ProjectPersistence` is their caller. They report state; they do not drive behavior.

---

## Effective Project-Entry Flow

_This is an effective mapping of the user-visible flow and its backend-side intent. It is not an atom-level implementation contract. Persistence remains the only direct caller of bootstrap surfaces — this describes what must effectively happen from a product and architecture standpoint._

### Creation

1. User submits the create project form
2. `POST /projects` is called — Persistence creates the project row and runs BS1
3. The response returns the generated public key
4. The UI surfaces the public key to the user and routes immediately to the project-specific page

### Project-specific page entry (same route for both post-creation and later re-entry)

The project-specific page always runs bootstrap verification on entry. What happens next depends on the result:

**If BS1 verification fails:**
- If the project is newly created and the project row exists, the backend automatically retries BS1 once
- If the retry succeeds, continue to the BS2 check
- If the retry fails, return an error to the user — no further follow-up for MVP

**If BS2 verification fails:**
- The most likely cause is that the user has not yet added the SSH key to their Git host — this applies equally to a newly created project and to a returning user who has not yet completed that step
- The user is shown `bootstrap.html` with the public key and instructions
- The user adds the key to their Git host and clicks continue
- Continue redirects back to the project-specific page, which runs verification again

**If both BS1 and BS2 verification pass:**
- Normal project workspace is shown

### Key points

- The project-specific page route is the single entry point for both post-creation and all subsequent visits
- BS1 is never run from the project-entry flow except as an automatic single retry on a newly created project where BS1 state is missing
- BS2 runs (via Persistence) when BS2 verification indicates the repository is not yet accessible — the verification failure informs the decision, and BS2 follows from it
- The UI never performs bootstrap checks itself — it follows the backend decision

---

## No Codebase Representation

The caller behavior and flow described on this page does not yet have accurate codebase representation. This page establishes the target ownership rules and concluded behavior as a foundation for implementation.
