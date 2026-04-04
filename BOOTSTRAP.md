# Bootstrap Rules

_Quick-reference overview of the bootstrap stages and their ownership._

_This file is intentionally compact. It exists to show **when bootstrap runs**, **who may call it**, **what each stage owns**, and **what is out of bounds**._

## Included Stages

| Stage | Current Surface | Core Purpose |
| --- | --- | --- |
| **BS1** | `repository_runtime/bootstrap/ProjectBootstrap.py` | Create local bootstrap storage and key material for a new project |
| **BS2** | `repository_runtime/bootstrap/ProjectBootstrap.py` | Turn a BS1-complete project into a real usable local repository with real branch state |
| **Bootstrap Verification** | `repository_runtime/bootstrap/ProjectBootstrap.py` | Report which bootstrap checks failed so caller-owned repair or redirect logic can decide what to do next |

## User-Facing Lifecycle

1. User creates project.
2. Persistence creates the project row and calls **BS1**.
3. User receives the generated public key and adds it on the Git host.
4. User returns to the project-specific page.
5. Project-specific page logic determines whether:
   - BS1 failed and bootstrap UI must be shown again
   - BS1 passed but BS2 is not complete, so BS2 should run
   - both stages are complete, so normal project page behavior may continue

## Allowed Caller Matrix

**Read this matrix as:**

- **Rows = caller**
- **Columns = target**

**Rule:** a layer named on the left may initiate communication toward a bootstrap surface named at the top.

| Caller \\ Target | BS1 | BS2 | Bootstrap Verification |
| --- | --- | --- | --- |
| **Persistence** | **Yes** | **Yes** | **Yes** |
| **Project Resolver** | No | No | No |
| **Project Runtime Binder** | No | No | No |
| **Bound Project Runtime** | No | No | No |
| **Execution** | No | No | No |
| **Routes / UI layer logic** | No direct call | No direct call | No direct call |

## Fast Rules

| Surface | Allowed | Not Allowed |
| --- | --- | --- |
| **BS1** | Create local bootstrap directories, generate SSH keypair, return bootstrap success/failure | Persist DB values, choose route/UI behavior, own repair policy |
| **BS2** | Use existing key access, materialize repo into `project_repo_directory`, fetch branch reality, derive resulting branch data | Commit DB values directly, own page redirect logic, act as a verification/reporting surface |
| **Bootstrap Verification** | Check resulting bootstrap state and return the first failure identifier for caller-owned follow-up | Drive route/UI output directly, mutate DB, replace bootstrap setup stages |

## Stage Details

### **BS1**

**Owns**

- creating `projects_base_directory` when needed
- creating `project_directory`
- creating `project_repo_directory`
- creating `project_ssh_directory`
- generating the project SSH keypair into the bootstrap-owned SSH directory

**May communicate with**

- shell-backed bootstrap helpers inside `repository_runtime/bootstrap/ProjectBootstrap.py`

**Must not own**

- project-row persistence
- route/UI decisions
- runtime binding
- execution behavior
- later repo materialization and branch discovery

### **BS2**

**Owns**

- using the existing SSH key to establish repo access
- materializing the repository into `project_repo_directory`
- fetching remote refs and materializing branch reality locally
- deriving resulting branch data from the real local repo state

**May communicate with**

- shell-backed bootstrap helpers inside `repository_runtime/bootstrap/ProjectBootstrap.py`

**Must not own**

- DB commits for `project.branch` or `project.branches`
- route/UI redirect decisions
- post-failure repair policy
- generalized verification/reporting behavior

### **Bootstrap Verification**

**Owns**

- reporting which bootstrap check failed
- returning bootstrap verification failure identifiers for caller-owned follow-up

**May communicate with**

- shell-backed bootstrap helpers inside `repository_runtime/bootstrap/ProjectBootstrap.py`

**Must not own**

- bootstrap setup itself
- persistence writes
- route/UI output shaping
- execution behavior

## Persistence Split

Persistence remains the owner of DB mutation around bootstrap.

**Persistence owns**

- creating the project row before BS1
- passing resolved bootstrap inputs into BS1 and BS2
- storing bootstrap-derived values on the project row
- persisting:
  - `project.branch`
  - `project.branches`
- commit / rollback behavior around bootstrap-triggered project mutation

**Persistence must not push DB ownership down into bootstrap**

- BS1 should not own project-row writes
- BS2 should not own project-row writes
- verification should not own project-row writes

## Important Clarifications

- **Bootstrap is not an internal layer in the normal resolver -> binder -> runtime -> execution chain.**
- **Bootstrap is a prerequisite/project-lifecycle surface.**
- **BS1 and BS2 are setup stages, not route surfaces.**
- **Verification is a reporting surface, not a repair surface.**
- **Routes and UI may decide whether bootstrap should be triggered, but they should not directly own bootstrap internals.**
- **Persistence is the caller and DB owner around bootstrap.**
- **BS2 returns resulting repo/branch reality; persistence decides what to store.**

## Practical Use

| Need | Correct Surface |
| --- | --- |
| create local bootstrap storage and SSH keys for a new project | **BS1** |
| turn a BS1-complete project into a real local repo with real branch state | **BS2** |
| know which bootstrap check failed so caller-owned follow-up can run | **Bootstrap Verification** |
| store resulting branch data on the project row | **Persistence** |
