# Bootstrap Rules

_Quick-reference overview of bootstrap stages and their ownership._

Source of truth: `BOOTSTRAP.md`

## Stages

| Stage | Surface | Core Purpose |
|---|---|---|
| **BS1** | `repository_runtime/bootstrap/bs1/bs1.py` | Create local storage and SSH key material for a new project |
| **BS2** | `repository_runtime/bootstrap/bs2/bs2.py` | Materialize the repository using the generated SSH key |
| **Bootstrap Verification** | `repository_runtime/bootstrap/__init__.py` | Report which bootstrap checks failed for caller-owned follow-up |

## User-Facing Lifecycle

1. User creates project
2. Persistence creates the project row and calls **BS1**
3. User receives generated public key and adds it on the Git host
4. UI routes the user to the project-specific page
5. Backend-owned project-entry logic determines:
   - BS1 failed → show bootstrap UI again
   - BS1 passed, BS2 not complete → run BS2
   - Both complete → continue to normal project page

The UI must follow the backend decision. It must not perform bootstrap checks itself.

## Allowed Caller Matrix

| Caller | BS1 | BS2 | Bootstrap Verification |
|---|---|---|---|
| **Persistence** | Yes | Yes | Yes |
| All other layers | No | No | No |

## Stage Ownership

### BS1

- Owns: create `projects_base_directory`, `project_directory`, `project_repo_directory`, `project_ssh_directory`, generate SSH keypair
- Must not own: project-row persistence, route/UI decisions, branch discovery

### BS2

- Owns: use existing SSH key to establish repo access, materialize repository into `project_repo_directory`
- Must not own: DB commits for `project.branch` or `project.branches`, route redirect decisions, branch discovery

### Bootstrap Verification

- Owns: check resulting bootstrap state, return first failure identifier for caller-owned follow-up
- Must not own: drive route/UI output directly, mutate DB, replace setup stages

## Key Rules

- **Branch discovery is not part of bootstrap.** `project.branch` and `project.branches` are post-BS2 concerns
- BS2 verification uses caller-supplied `remote_repo_url` for origin check — that is project metadata, not bootstrap-path data
- BS outputs must stay narrow: repo_path, ssh_key, public_key_path are the useful outputs to persistence
- Bootstrap repair and recovery policy belong to the project-entry decision surface, not to bootstrap stages
