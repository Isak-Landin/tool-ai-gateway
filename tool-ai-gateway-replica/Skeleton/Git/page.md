# Git

The `repository_runtime/git/` subpackage owns project-scoped git transport and shell-backed git operations.

## Modules

### PersistentShell

Provides a persistent shell session for a repository directory. Used as the transport layer for all git operations in a project runtime.

- Bound to one `repo_path`
- Runs commands in that directory context
- Managed lifecycle: opened at binding time, closed at runtime teardown

### GitHub class

Wraps git CLI operations needed for project repository interaction:

- clone
- fetch
- branch operations
- remote verification

### `run_git_probe`

Low-level git probe used by `FileRuntime` for read-only git operations (e.g. `git show`, `git grep`). Returns `(exit_code, stdout_string)`.

## Binding Chain

The binder creates a `RepositoryRuntime` which wraps a `PersistentShell`. The shell is scoped to the project's `repo_path`. Execution accesses git transport exclusively through `FileRuntime`, which composes the shell via `run_git_probe`.

## Ownership

- Git transport is lower-layer/runtime-owned
- `FileRuntime` is the intended live file/tree/search owner; callers must not unwrap back to `RepositoryRuntime` directly
- `RepositoryRuntime` remains shell/git transport only and explicitly fails if called as a live file/tree owner
