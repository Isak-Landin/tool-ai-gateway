# Bootstrap Target Map

_Target-state ownership map for bootstrap-related surfaces, including existing and not-yet-existing responsibilities._

## NOW: BS usefulness alignment with persistence

These are the current BS-side alignment points that matter **now** before moving deeper into persistence work.

1. **Keep BS outputs narrow.**
   - BS1 usefulness to persistence is: make it possible for persistence to write `repo_path`, `ssh_key`, and `public_key_path`.
   - BS2 usefulness to persistence is: make the repo materially usable locally.
   - Bootstrap verification usefulness to persistence is: report whether BS1/BS2 state is valid.
   - **Why:** these are the bootstrap-side results later consumers actually rely on in `db/models.py`, `persistence/ProjectPersistence/ProjectPersistence.py`, `persistence/BoundProjectRuntimePersistence/BoundProjectRuntimePersistence.py`, and `ProjectRuntimeBinder/ProjectRuntimeBinder.py`.

2. **Do not add branch discovery to bootstrap.**
   - `project.branch` and `project.branches` are needed later by runtime binding and branch-aware runtime behavior.
   - They still do **not** belong to BS1, BS2, or bootstrap verification.
   - **Why:** branch reality is a separate post-BS2 concern, and pushing it into bootstrap would blur the split already established in this map and in `db/models.py`.

3. **Keep BS verification dependent on authoritative caller-owned metadata.**
   - BS2 verification must use caller-supplied `remote_repo_url` for the `origin` check.
   - Bootstrap path derivation must stay path-only.
   - **Why:** `remote_repo_url` is project metadata, not bootstrap-path data; the caller-owned seam is what lets persistence use verification without inventing or persisting the wrong thing. See `repository_runtime/bootstrap/__init__.py`, `repository_runtime/bootstrap/bs2/bs2.py`, and `persistence/ProjectPersistence/ProjectPersistence.py`.

4. **Only BS-local cleanup/refactor work should remain inside bootstrap.**
   - Any remaining bootstrap refactor should be about keeping BS1, BS2, and verification contracts clean and non-misleading.
   - It should not expand BS ownership into persistence, branch discovery, route decisions, or repair policy.
   - **Why:** full bootstrap usefulness to persistence comes from a clean contract boundary, not from pushing more lifecycle work into bootstrap.

### Notes

- `api_routes/project_routes/router.py` still contains a placeholder for project-entry bootstrap verification logic. That is not a bootstrap-layer gap; it is a higher-layer integration gap.
- `ProjectPersistence.create_project(...)` currently covers BS1 only; it does not yet implement the final project-entry / BS2 / post-BS2 branch-discovery lifecycle.
- `db/models.Project.branch` still has a default of `"main"`, and `ProjectPersistence.update_project(...)` still allows direct branch mutation. Those behaviors should not be mistaken for final branch-reality alignment.

## Existing encapsulated bootstrap surfaces

### Project-specific page entry bootstrap decision

**Owns**

- deciding whether normal project-page flow may continue
- deciding whether bootstrap UI must be shown again
- deciding whether BS2 should run now
- deciding whether the user must stay in bootstrap flow
- acting as the backend/API-side decision surface that the UI route follows

**Must not own**

- bootstrap implementation details
- project-row writes
- bootstrap helper execution
- UI-route-local bootstrap logic

### Persistence caller for `bs1(...)`

**Owns**

- creating the project row before BS1
- deriving authoritative bootstrap inputs
- passing resolved bootstrap inputs into `bs1(...)`
- storing resulting bootstrap-derived DB values after BS1 succeeds
- commit / rollback around BS1-triggered project-row mutation
- writing the BS1-derived project fields needed later by runtime binding:
  - `repo_path`
  - `ssh_key`
  - `public_key_path`

**Must not push down into `bs1(...)`**

- DB mutation ownership
- route-facing decisions
- page-flow decisions

### `bs1(...)`

**Owns**

- composing BS1 setup from bootstrap-local helpers
- creating local bootstrap storage
- generating the project SSH keypair
- stage-local cleanup of `project_directory` when BS1 fails

**Must not own**

- project-row writes
- commit / rollback behavior
- route or UI redirect decisions
- later repository materialization
- later branch discovery/storage

### `_verify_bs1(...)`

**Owns**

- checking resulting BS1 state after BS1 should have completed
- returning the first BS1 verification failure identifier
- staying limited to verification/reporting of resulting BS1 state

**Must not own**

- BS1 setup itself
- project-row writes
- repair execution
- route or UI output shaping

### Persistence caller for `bs2(...)`

**Owns**

- deciding when BS2 should be called
- passing authoritative bootstrap inputs into `bs2(...)`
- deciding what should happen after BS2 success or failure
- commit / rollback around BS2-triggered project-row mutation when BS2 later requires it
- passing authoritative `remote_repo_url` as project metadata into BS2 / BS2 verification

**Must not push down into `bs2(...)`**

- DB mutation ownership
- route-facing decisions
- page-flow decisions

### `bs2(...)`

**Owns**

- using the existing SSH key to establish repository access
- materializing the repository into `project_repo_directory`

**Must not own**

- project-row writes
- commit / rollback behavior
- route or UI redirect decisions
- verification reporting
- repair policy
- deriving/storing the real branch list as persisted project data
- deriving/storing the effective default branch as persisted project data

### Persistence caller for bootstrap verification

**Owns**

- deciding when bootstrap verification should run
- passing authoritative project-scoped bootstrap inputs into verification
- receiving the first failure result from verification
- deciding what follow-up should happen from that failure

**Must not push down into verification**

- DB mutation ownership
- repair policy ownership
- route/UI control ownership

### `_verify_bs2(...)`

**Owns**

- checking resulting BS2 state after BS2 should have completed, limited to:
  - verifying `project_repo_directory` is a real git repository via `git rev-parse --is-inside-work-tree`
  - verifying `origin` matches the expected `remote_repo_url` via `git remote get-url origin`
  - verifying the remote is reachable with the current SSH key via `git ls-remote --heads origin`
- returning the first BS2 verification failure identifier
- staying limited to verification/reporting of resulting BS2 state

**Must not own**

- BS2 setup itself
- project-row writes
- repair execution
- route or UI output shaping
- later branch-discovery/storage responsibilities

### `verify_bs_all(...)`

**Owns**

- sequencing BS1 verification before BS2 verification
- returning the first bootstrap verification failure from the composed verification stages

**Must not own**

- BS1 setup
- BS2 setup
- project-row writes
- repair execution

## Existing internal bootstrap-local surfaces

### `repository_runtime/bootstrap/common/common.py`

**Owns**

- shared bootstrap-local shell command helpers
- bootstrap-local strict command failure translation through `ProjectBootstrapError`
- bootstrap-local raw command `(code, output)` access for verification-oriented bootstrap work

**Must not own**

- project-row persistence
- git-command semantics
- route/UI flow decisions

## Not-yet-existing but required/non-bootstrap surfaces

### Separate branch-discovery / branch-reality derivation surface

**Owns**

- deriving the real branch list from the usable local repository
- deriving the effective/default branch candidate from the usable local repository
- returning branch-reality data outward to its caller

**Must not own**

- BS1 setup
- BS2 setup
- project-row writes
- route/UI flow decisions

### Persistence caller for branch discovery

**Owns**

- deciding when branch discovery should run
- passing the usable local-repository inputs into branch discovery
- receiving derived branch reality
- storing:
  - `project.branch`
  - `project.branches`

**Must not push down into branch discovery**

- DB mutation ownership
- route/UI flow decisions

## Cross-surface certainties

- `_derive_project_storage_paths_for_bootstrap(...)` is path-only and must stay path-only
- `remote_repo_url` is project metadata, not bootstrap-path data
- route serializers must not be reused as bootstrap/runtime transport shapes just to avoid adding the correct caller-owned seam
- BS1 is bootstrap setup
- BS2 is bootstrap setup
- bootstrap verification is reporting only
- branch discovery/storage does not have to belong to BS2
- project-row field mapping currently resolves as:
  - before BS1/create-row: `name`, `remote_repo_url`
  - after BS1 persistence write: `repo_path`, `ssh_key`, `public_key_path`
  - after separate post-BS2 branch discovery: `branch`, `branches`
- `branch` and `branches` are needed later by runtime binding and branch-aware runtime behavior, but they are not bootstrap outputs
