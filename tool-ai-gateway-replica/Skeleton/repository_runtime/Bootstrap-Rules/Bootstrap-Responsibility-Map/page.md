# Bootstrap Responsibility Map

_Target-state ownership map for bootstrap-related surfaces._

Source of truth: `BOOTSTRAP_TARGET_MAP.md`

## BS Alignment Points (Current Priority)

1. **Keep BS outputs narrow**
   - BS1 → persistence writes `repo_path`, `ssh_key`, `public_key_path`
   - BS2 → makes the repo materially usable locally
   - Bootstrap verification → reports whether BS1/BS2 state is valid
   - These are the bootstrap-side results that `db/models.py`, `ProjectPersistence`, `BoundProjectRuntimePersistence`, and `ProjectRuntimeBinder` rely on

2. **Branch discovery does not belong to bootstrap**
   - `project.branch` and `project.branches` are post-BS2 concerns
   - Pushing them into bootstrap would blur the established split

3. **Bootstrap verification uses caller-supplied `remote_repo_url`**
   - `remote_repo_url` is project metadata, not bootstrap-path data
   - The caller-owned seam lets persistence use verification without inventing or persisting the wrong thing

4. **Only BS-local cleanup should remain inside bootstrap**
   - No expansion into persistence, branch discovery, route decisions, or repair policy

## Encapsulated Ownership Map

### Project-entry bootstrap decision surface (not yet implemented)

- Owns: deciding whether normal flow continues, whether bootstrap UI must show again, whether BS2 should run now
- Must not own: bootstrap implementation, project-row writes, bootstrap helper execution, UI-local bootstrap logic

### Persistence caller for `bs1(...)`

- Owns: creating the project row before BS1, deriving authoritative bootstrap inputs, passing resolved inputs into `bs1(...)`, storing BS1-derived DB values, commit/rollback around mutation
- Must not push into BS1: DB mutation ownership, route/page flow decisions

### `bs1(...)`

- Owns: composing BS1 from bootstrap-local helpers, creating local bootstrap storage, generating SSH keypair
- Must not own: project-row persistence, DB mutation, route decisions

### `bs2(...)`

- Owns: using SSH key, materializing repository into `project_repo_directory`
- Must not own: DB commits for branch data, route decisions, branch discovery

### Bootstrap Verification

- Owns: returning first failure identifier from BS state checks
- Must not own: driving route output, mutating DB
