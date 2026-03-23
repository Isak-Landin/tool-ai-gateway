# Internal Layer Rules

_Quick-reference overview of the **five internal layers** below API routes._

_This file is intentionally compact. It exists to show **who may talk to whom**, **who owns what**, and **what is out of bounds**._

## Included Layers

| Layer | Current Surface | Core Purpose |
| --- | --- | --- |
| **Project Resolution** | `project_resolution.py` | Resolve an existing project row for project-scoped work |
| **Runtime Binding** | `runtime_binding.py` | Turn a resolved project row into a usable bound runtime |
| **Project Handle** | `project_handle.py` | Hold one project-scoped runtime and its bound accessors/executors |
| **Execution** | `execution.py` | Run project-scoped workflow logic |
| **Persistence** | `persistence/` | Read and write database-backed state and scoped repo/file state |

## Intended Flow

**Project Resolution** -> **Runtime Binding** -> **Project Handle** -> **Execution** -> **Persistence**

Return flow is the reverse direction:

**Persistence** -> **Execution** -> **Project Handle** -> **Runtime Binding** -> caller above these layers

## Allowed Interaction Matrix

**Rule:** row layer initiates communication toward column layer.

| Caller \\ Target | Project Resolution | Runtime Binding | Project Handle | Execution | Persistence |
| --- | --- | --- | --- | --- | --- |
| **Project Resolution** | — | No | No | No | **Yes** |
| **Runtime Binding** | No | — | **Yes** | No | **Yes** |
| **Project Handle** | No | No | — | No | No |
| **Execution** | No | No | **Yes** | — | **Yes** |
| **Persistence** | No | No | No | No | — |

## Fast Rules

| Layer | Allowed | Not Allowed |
| --- | --- | --- |
| **Project Resolution** | Read project-scoped rows from persistence | Build runtime, bind services, execute workflow |
| **Runtime Binding** | Construct `ProjectHandle`, bind accessors/executors, read runtime-needed persistence fields | Resolve projects, run workflow logic, shape route responses |
| **Project Handle** | Store project-scoped runtime state and bound dependencies | Resolve, bind, persist, or execute by itself |
| **Execution** | Use `ProjectHandle`, load/persist execution state, assemble context, call model/tools/runtime surfaces | Resolve projects, construct runtime, shape HTTP/API responses |
| **Persistence** | Serve storage and repo/file access needs for higher layers | Orchestrate workflow, bind runtime, call back upward |

## Layer Details

### **Project Resolution**

**Owns**

- project existence checks
- project row lookup by `project_id`
- handing a resolved project shape upward

**May communicate with**

- **Persistence**

**Must not communicate with**

- **Runtime Binding**
- **Project Handle**
- **Execution**

### **Runtime Binding**

**Owns**

- turning a resolved project row into a usable runtime
- attaching project-scoped accessors and executors
- returning one bound `ProjectHandle`

**May communicate with**

- **Project Handle**
- **Persistence**

**Must not communicate with**

- **Project Resolution**
- **Execution**

### **Project Handle**

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
- context assembly
- model/tool/runtime sequencing
- execution-owned persistence ordering

**May communicate with**

- **Project Handle**
- **Persistence**

**Must not communicate with**

- **Project Resolution**
- **Runtime Binding**

### **Persistence**

**Owns**

- database-backed reads and writes
- execution/history/file storage surfaces
- scoped repository file access

**May communicate with**

- no internal layer upward; it is a **serving layer**

**Must not own**

- orchestration
- runtime construction
- project resolution policy
- response shaping

## Important Clarifications

- **Project Handle is not an orchestrator.** It is a bound runtime container.
- **Execution is the first layer that may orchestrate.**
- **Persistence serves downward-only concerns.** It should not drive workflow.
- **Runtime Binding may prepare runtime dependencies, but must not perform execution work.**
- **Project Resolution stays narrow.** It resolves; it does not enrich into runtime behavior.

## Practical Use

If a change needs to:

| Need | Correct Layer |
| --- | --- |
| find a project by `project_id` | **Project Resolution** |
| attach git/files/messages onto a project runtime | **Runtime Binding** |
| hold bound runtime state during a project-scoped run | **Project Handle** |
| run chat/tool/model workflow | **Execution** |
| read/write rows or scoped repo files | **Persistence** |

