# Internal Layer Rules

_Quick-reference overview of the **five internal layers** below API routes._

_This file is intentionally compact. It exists to show **who may talk to whom**, **who owns what**, and **what is out of bounds**._

## Included Layers

| Layer | Current Surface | Core Purpose |
| --- | --- | --- |
| **Project Resolver** | `ProjectResolver/` | Resolve an existing project row for project-scoped work |
| **Project Runtime Binder** | `ProjectRuntimeBinder/` | Turn a resolved project row into a usable bound runtime |
| **Bound Project Runtime** | `BoundProjectRuntime/` | Hold one project-scoped runtime and its bound dependencies |
| **Execution** | `execution/` | Run project-scoped workflow logic |
| **Persistence** | `persistence/` | Read and write database-backed state and scoped repo/file state |

## Intended Flow

**Project Resolver** -> **Project Runtime Binder** -> **Bound Project Runtime** -> **Execution** -> **Persistence**

Return flow is the reverse direction:

**Persistence** -> **Execution** -> **Bound Project Runtime** -> **Project Runtime Binder** -> caller above these layers

## Allowed Interaction Matrix

**Read this matrix as:**

- **Rows = caller**
- **Columns = target**

**Rule:** a layer named on the left may initiate communication toward a layer named at the top.

| Caller \\ Target | Project Resolver | Project Runtime Binder | Bound Project Runtime | Execution | Persistence |
| --- | --- | --- | --- | --- | --- |
| **Project Resolver** | — | No | No | No | **Yes** |
| **Project Runtime Binder** | No | — | **Yes** | No | **Yes** |
| **Bound Project Runtime** | No | No | — | No | No |
| **Execution** | No | No | **Yes** | — | **Yes** |
| **Persistence** | No | No | No | No | — |

## Fast Rules

| Layer | Allowed | Not Allowed |
| --- | --- | --- |
| **Project Resolver** | Read project-scoped rows from persistence | Build runtime, bind services, execute workflow |
| **Project Runtime Binder** | Construct `BoundProjectRuntime`, bind dependencies, read runtime-needed persistence fields | Resolve projects, run workflow logic, shape route responses |
| **Bound Project Runtime** | Store project-scoped runtime state and bound dependencies | Resolve, bind, persist, or execute by itself |
| **Execution** | Use `BoundProjectRuntime`, load/persist execution state, process ordered project messages, assemble bounded recent project context, load selected context from the bound local repo, choose context deterministically, call one execution model and execution-scoped runtime/tool surfaces | Resolve projects, construct runtime, shape HTTP/API responses |
| **Persistence** | Serve storage needs for higher layers, including required MVP message/history persistence and any persistence-backed file/archive storage | Orchestrate workflow, bind runtime, act as the route-serving owner directly, call back upward |

## Layer Details

### **Project Resolver**

**Owns**

- project existence checks
- project row lookup by `project_id`
- handing a resolved project shape upward

**May communicate with**

- **Persistence**

**Must not communicate with**

- **Project Runtime Binder**
- **Bound Project Runtime**
- **Execution**

### **Project Runtime Binder**

**Owns**

- turning a resolved project row into a usable runtime
- attaching project-scoped dependencies
- returning one bound `BoundProjectRuntime`

**May communicate with**

- **Bound Project Runtime**
- **Persistence**

**Must not communicate with**

- **Project Resolver**
- **Execution**

### **Bound Project Runtime**

**Owns**

- holding one resolved/bound project runtime
- exposing bound dependencies to the execution layer
- resource cleanup for bound executors when relevant

**May communicate with**

- no internal layer directly; it is a **holder surface**

**Must not own**

- persistence reads/writes
- resolution
- binding logic
- workflow logic

### **Execution**

**Owns**

- workflow ordering
- bounded recent project context assembly
- selected context loading from the bound local repository state
- deterministic context selection for the current run
- model/tool/runtime sequencing
- execution-owned persistence ordering
- one execution-model run flow for MVP
- execution-scoped use of repository runtime tools where the behavior is truly execution/tool-only
- direct use of `ExecutionPersistence` for bounded recent history, next-sequence loading, and ordered artifact writes

**May communicate with**

- **Bound Project Runtime**
- **Persistence**

**Must not communicate with**

- **Project Resolver**
- **Project Runtime Binder**

**Architectural deprecation to remember**

- direct execution use of repository tree/search helpers should not remain the general owner for non-execution file/tree consumers once the dedicated bound file surface exists
- direct execution use of general route/shared message-history reads should not replace the intended bound message surface

### **Persistence**

**Owns**

- database-backed reads and writes
- execution/history/file storage surfaces
- persistence-backed file/archive storage surfaces
- message/history persistence surfaces reused by execution and bound message-serving runtime dependencies

**May communicate with**

- no internal layer upward; it is a **serving layer**

**Must not own**

- orchestration
- runtime construction
- project resolution policy
- response shaping

## Important Clarifications

- **Bound Project Runtime is not an orchestrator.** It is a bound runtime container.
- **Execution is the first layer that may orchestrate.**
- **Execution chooses bounded context for MVP.** Full project history may stay in DB, but execution should not send all of it by default.
- **Execution must process persisted project messages for MVP.** Message loading and message persistence are part of the required MVP run flow.
- **Execution keeps message-selection policy.** Bounded recent-history limits remain execution-owned even after a bound message surface exists.
- **Persistence serves downward-only concerns.** It should not drive workflow.
- **Project Runtime Binder may prepare runtime dependencies, but must not perform execution work.**
- **Project Resolver stays narrow.** It resolves; it does not enrich into runtime behavior.
- **Shell-backed tools run from one bound project shell.** Binder binds it, execution uses it.
- **A dedicated bound file/message surface may sit on BoundProjectRuntime without making execution or persistence the general owner of route-serving project reads.**

## Surface Shape Guidance

- Each layer should aim to expose a **small intentional top-level surface**.
- That top-level surface should represent the layer's reachable contract, not all internal machinery.
- Shared implementation logic may live in internal helpers or submodules without becoming part of the public layer contract.
- When a layer needs privileged or use-specific operations, group them into clearly named submodules rather than mixing them into one flat surface.
- Naming should reflect ownership and intended usage, so drift feels wrong before tests or review catch it.

Examples of acceptable shape direction:

- top-level layer entrypoints that describe the layer's main intended usage
- grouped submodules for privileged or ownership-specific operations such as `for_execution` or `for_runtime_binding`
- internal helper modules that support the layer without redefining its public meaning

This is preferred over broad caller-identity enforcement. The main goal is to make the correct reachable surface obvious, small, and structurally hard to misuse.

## Practical Use

If a change needs to:

| Need | Correct Layer |
| --- | --- |
| find a project by `project_id` | **Project Resolver** |
| attach execution-needed dependencies onto a project runtime | **Project Runtime Binder** |
| hold bound runtime state during a project-scoped run | **Bound Project Runtime** |
| run chat/tool/model workflow with bounded recent project context | **Execution** |
| read/write rows or scoped repo files | **Persistence** |
