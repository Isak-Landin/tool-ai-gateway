# ProjectRuntimeBinder — Binding Chain

Covers `BoundProjectRuntime/`, `ProjectResolver/`, and `ProjectRuntimeBinder/` as one conceptual unit.

---

## BoundProjectRuntime

`BoundProjectRuntime/BoundProjectRuntime.py`

A passive runtime holder. Stores project identity fields and bound dependencies. Does not resolve, bind, persist, or orchestrate by itself.

### Stores

- `project_id`, `name`, `repo_path`, `remote_repo_url`, `branch`, `branches`, `key_path`
- `_repository_runtime` — bound via `bind_repository_runtime(...)`
- `model_context` — reserved for future project-scoped context management

### Accessors

- `require_repository_runtime()` — returns the bound repo runtime or raises
- `is_repository_runtime_bound()` — boolean check
- `close()` — propagates cleanup to bound resources
- Direct `.repository_runtime` access raises by design — callers must use `require_repository_runtime()`

---

## ProjectResolver

`ProjectResolver/ProjectResolver.py`

Resolves a project row by `project_id`. Returns a resolution-shaped dict for handoff to the binder.

- Uses `ResolutionPersistence` internally
- Raises `ProjectNotFoundError` if the project does not exist
- Stays narrow: resolves only, does not enrich into runtime behavior

---

## ProjectRuntimeBinder

`ProjectRuntimeBinder/ProjectRuntimeBinder.py`

Turns a resolved project dict into a `BoundProjectRuntime` with attached dependencies.

### Steps

1. Extract `project_id` from resolved project
2. Load runtime-binding fields from `RuntimeBindingPersistence`
3. Determine effective branch (stored or override)
4. Construct `BoundProjectRuntime` from project row
5. Create and bind a `RepositoryRuntime` (wraps `PersistentShell`)
6. Validate preconditions — raises `ProjectRuntimeBindingError` if anything is missing

### Ownership

- The binder attaches dependencies; it does not perform execution work
- Accepts optional `branch_override` to support per-request branch switching
- Does not resolve the project (that is `ProjectResolver`'s job)
- Does not decide what the run should do (that is `Execution`'s job)

---

## Current State

The full binding chain is implemented and in production use:

```
ProjectResolver.resolve_by_id(project_id)
  → ProjectRuntimeBinder.bind(resolved_project, branch_override=None)
    → BoundProjectRuntime (with RepositoryRuntime attached)
```

Routes call this chain through `api_routes/project_routes/runtime.py`.
