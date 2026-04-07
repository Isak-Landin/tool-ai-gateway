# Skeleton — Internal Layer Rules

_Quick-reference overview of the five internal layers below API routes._

Source of truth: `LAYER_RULES.md`

## Included Layers

| Layer | Module | Core Purpose |
|---|---|---|
| **Project Resolver** | `ProjectResolver/` | Resolve an existing project row for project-scoped work |
| **Project Runtime Binder** | `ProjectRuntimeBinder/` | Turn a resolved project row into a usable bound runtime |
| **Bound Project Runtime** | `BoundProjectRuntime/` | Hold one project-scoped runtime and its bound dependencies |
| **Execution** | `execution/` | Run project-scoped workflow logic |
| **Persistence** | `persistence/` | Read and write database-backed state and scoped repo/file state |

## Intended Flow

**Project Resolver** → **Project Runtime Binder** → **Bound Project Runtime** → **Execution** → **Persistence**

Return flow is the reverse.

## Allowed Interaction Matrix

| Caller \ Target | Project Resolver | Project Runtime Binder | Bound Project Runtime | Execution | Persistence |
|---|---|---|---|---|---|
| **Project Resolver** | — | No | No | No | **Yes** |
| **Project Runtime Binder** | No | — | **Yes** | No | **Yes** |
| **Bound Project Runtime** | No | No | — | No | No |
| **Execution** | No | No | **Yes** | — | **Yes** |
| **Persistence** | No | No | No | No | — |

## Fast Rules

| Layer | Allowed | Not Allowed |
|---|---|---|
| **Project Resolver** | Read project-scoped rows from persistence | Build runtime, bind services, execute workflow |
| **Project Runtime Binder** | Construct BoundProjectRuntime, bind dependencies, read runtime-needed persistence fields | Resolve projects, run workflow logic, shape route responses |
| **Bound Project Runtime** | Store project-scoped runtime state and bound dependencies | Resolve, bind, persist, or execute by itself |
| **Execution** | Use BoundProjectRuntime, load/persist execution state, process ordered messages, assemble bounded recent context, call one execution model | Resolve projects, construct runtime, shape HTTP responses, own live lower-layer file/tree/search reads outside bound objects |
| **Persistence** | Serve storage needs for higher layers | Orchestrate workflow, bind runtime, act as route-serving owner directly, call back upward |

## Important Clarifications

- `BoundProjectRuntime` is a holder, not an orchestrator
- `Execution` is the first layer that may orchestrate
- `FilesRepository` and `RepositoryRuntime` are not live file owners — use `FileRuntime`
- `MessagesRepository` is not a shared history owner — use `MessageRuntime` functions
- Shell-backed tools run from one bound project shell bound by the binder
- Route-facing code should prefer a narrowed route runtime helper for file-serving; message history via `MessageRuntime` functions

## Practical Use

| Need | Correct Layer |
|---|---|
| Find a project by `project_id` | **Project Resolver** |
| Attach execution-needed dependencies onto a project runtime | **Project Runtime Binder** |
| Hold bound runtime state during a run | **Bound Project Runtime** |
| Run chat/tool/model workflow with bounded recent project context | **Execution** |
| Read/write rows or scoped repo files | **Persistence** |
