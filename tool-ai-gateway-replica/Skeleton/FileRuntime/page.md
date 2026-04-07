# FileRuntime

`FileRuntime/FileRuntime.py` — function module for project-scoped live file operations.

## Purpose

Composes caller-supplied `repository_runtime` and `files_repository` dependencies into route-usable and execution-usable file operations. Owns live file/search behavior, ignore-path enforcement, and error translation.

Does **not** own: repository runtime construction, branch selection policy, or file-row persistence internals.

## Public Functions

| Function | Purpose |
|---|---|
| `read_file(repo_rt, *, branch, relative_repo_path, start_line, number_of_lines, end_line)` | Read file content from git branch via `git show` |
| `search_text(repo_rt, *, branch, query, relative_repo_path, case_sensitive, max_results)` | Search text in branch via `git grep` |
| `list_persisted_files(files_repo)` | List file snapshot rows from persistence |
| `get_persisted_file(files_repo, relative_repo_path)` | Get one file snapshot row by path |
| `persist_file_snapshot(repo_rt, files_repo, *, branch, relative_repo_path)` | Read live file and upsert snapshot row |
| `get_ignore_patterns()` | Return current repository ignore patterns |

## Usage Pattern

All live-read functions require an explicit `repository_runtime` dependency. The caller does not instantiate git directly — they pass the bound `RepositoryRuntime` from `BoundProjectRuntime`.

```python
from FileRuntime import read_file, search_text

repo_rt = bound_runtime.require_repository_runtime()
result = read_file(repo_rt, branch="main", relative_repo_path="/src/app.py")
```

## Ignore Paths

`FileRuntime` enforces `repository_tools` ignore patterns on all read and search operations. Ignored paths raise `FileRuntimeError`.

## Ownership

- `FileRuntime` is the lower live owner for project-scoped file reads, tree reads, and branch-aware repository access
- `RepositoryRuntime` is transport only — callers must not unwrap `FileRuntime` back to `RepositoryRuntime`
- `FilesRepository` is persistence-shaped storage only — not a live file owner
- Execution uses `FileRuntime.read_file` and `FileRuntime.search_text` for selected context
- Routes use `FileRuntime` for tree, file, and search endpoints

## Pending / Excluded

- `list_tree(...)` — excluded; behavior spans multiple owners, reintroduce after lower ownership split is clarified
- `load_selected_context(...)` — excluded; appears execution-shaped, long-term owner should be confirmed first

## Error Translation

Lower git/persistence failures are translated to `FileRuntimeError` at this surface.
