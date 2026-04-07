# repository_runtime

The `repository_runtime/` package owns the project-scoped repository transport layer.

## Structure

```
repository_runtime/
├── RepositoryRuntime.py    — main runtime class
├── bootstrap/
│   ├── bs1/                — bootstrap step 1 (storage setup)
│   └── bs2/                — bootstrap step 2 (repository verification)
├── git/                    — git probe helpers
├── inspection/             — repository inspection utilities
└── shell/                  — PersistentShell
```

## RepositoryRuntime

Wraps a `PersistentShell` scoped to one `repo_path`. Provides the transport surface for git operations.

- Bound during `ProjectRuntimeBinder.bind(...)` — one runtime per project run
- Accessed via `BoundProjectRuntime.require_repository_runtime()`
- Used by `FileRuntime` via `run_git_probe` for all live file/tree/search reads
- Transport only — not a live file owner; fails explicitly if used as one

## bootstrap/

Owns the two-step bootstrap process for new projects:

- **BS1** — project storage setup (creates project row, SSH key material, deploys public key)
- **BS2** — repository verification (clones/verifies the remote repository is accessible)

Bootstrap is not part of the normal per-request lifecycle. See `Bootstrap Rules` for ownership and verification boundaries.

## Ownership

- Shell/git transport is lower-layer/runtime-owned
- `FileRuntime` is the intended live file/tree/search surface — callers must use it, not unwrap to `RepositoryRuntime`
- Branch discovery is not part of bootstrap; it remains a missing backend route surface
