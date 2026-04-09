# repository_runtime

_Idea development tracking for the repository_runtime module._

---

# Confirmed

## API

**Verify counterparts — caller rules**

`_verify_bs1(...)`, `_verify_bs2(...)`, and `verify_bs_all(...)` do not follow the same restricted caller rules as BS1 and BS2. They are permitted to be called by API routes, persistence, and internally by BS2 (which calls `_verify_bs1` as a precondition before cloning). They are reporting utilities only — they check state and return a `(bool, failure_enum | None)` tuple. They never run setup and never mutate anything.

## BoundProjectRuntime

## db

## execution

## FileRuntime

## MessageRuntime

## ollama

## persistence

**BS1 — callable by persistence only**

BS1 creates all local bootstrap storage for a new project and generates the SSH keypair. It owns:
- Creating `projects_base_directory`, `project_directory`, `project_repo_directory`, `project_ssh_directory`
- Generating the project SSH keypair into the SSH directory
- Stage-local cleanup of `project_directory` on failure

Raises `ProjectBootstrapError` on failure. Returns `True` on success. Takes `project_paths` dict and `shell`.

Rule: callable by `ProjectPersistence` only. No other layer may call `bs1(...)` directly.

---

**BS2 — callable by persistence only**

BS2 takes a BS1-complete project and materializes the remote repository locally. It owns:
- Internally verifying BS1 state before proceeding (calls `_verify_bs1` as a precondition)
- Cloning the remote repository into `project_repo_directory` using the project SSH key

Raises `ProjectBootstrapError` on failure. Returns `True` on success. Takes `project_paths` dict, `shell`, and `remote_repo_url`.

Rule: callable by `ProjectPersistence` only. No other layer may call `bs2(...)` directly.

## ProjectResolver

## ProjectRuntimeBinder

## repository_tools

## ui

## web_search

---

# Being Developed

## API

**Route responder and caller workflow — effective overview**

The following describes the effective workflow from route to persistence for bootstrap-related project entry. This is an intent map, not a final implementation contract.

On every request to the project-specific page (`GET /projects/<project_id>`), the following must effectively occur:

1. Bootstrap verification runs (`verify_bs_all` or individual verify calls)
2. If BS1 verification fails → the persistence BS1 responder is invoked with the failure enum. It performs its own DB and disk checks and decides whether to re-run BS1 or return an error.
3. If BS2 verification fails → the persistence BS2 responder is invoked with the failure enum. It performs its own DB and disk checks and decides whether to run BS2, clean and re-run, or surface bootstrap guidance to the user.
4. If both pass → normal workspace flow continues.

**Middle man between route and persistence:**

For MVP, whether this decision logic is called directly by the route or through a dedicated middle-man surface is uncertain. Direct route-to-persistence calling is the simpler MVP path, but it may not survive a clean architecture review.

For final intent, a dedicated project-entry decision surface sits between the route and persistence. It owns the decision of what to do with verification results. The route follows its response. Persistence is called only by this surface, not by the route directly.

Both the MVP path and the final-intent path represent the same workflow — the difference is whether the decision logic lives in the route itself or in a named intermediate surface.

## BoundProjectRuntime

## db

## execution

## FileRuntime

## MessageRuntime

## ollama

## persistence

## ProjectResolver

## ProjectRuntimeBinder

## repository_tools

## ui

## web_search

---

# Uncertain

## API

## BoundProjectRuntime

## db

## execution

## FileRuntime

## MessageRuntime

## ollama

## persistence

## ProjectResolver

## ProjectRuntimeBinder

## repository_tools

## ui

## web_search
