# Runtime Workflow — Plain Language

_The five internal layers described as concepts, not code._

Source of truth: `LAYER_INTENT.md`

## Layer 1 — Project Resolver

**"Which project is this request talking about?"**

Confirms the project exists and hands its identity upward. Nothing more.

Does not build runtime, execute workflow, or shape responses.

## Layer 2 — Project Runtime Binder

**"Given this project, what dependencies should be attached so runtime work can happen?"**

Turns a resolved project into a usable runtime surface by attaching:
- project-scoped persistence surfaces
- project-scoped repository execution surfaces

Does not decide what the workflow does. Does not resolve the project. Does not own live lower-layer file/tree/search reads outside bound objects like `FileRuntime`.

## Layer 3 — Bound Project Runtime

A project-scoped runtime container. Passive.

Holds:
- which project is active
- which branch / repository root is active
- which project-scoped dependencies are already attached

Not an orchestrator. Not a decision-maker. Just the runtime object that later decisions operate on.

## Layer 4 — Execution

**"Now that we have a usable project runtime, what should happen in what order?"**

The first layer that actually runs project-scoped workflow. Owns:
- runtime ordering
- context assembly
- message processing
- model and tool sequencing
- execution-owned persistence ordering
- deciding when the run is finished

Does not identify the project, bind the runtime, shape transport responses, or pretend to be raw storage.

## Layer 5 — Persistence

**"How do we read or write the state that higher layers need?"**

The serving layer for stored state. Owns reading/writing entities. Does not decide workflow.

Current clarification:
- `FilesRepository` is persistence-shaped DB storage only — not a live file owner
- `FileRuntime` is the live owner for file reads, tree reads, and branch-aware repository access
- `MessagesRepository` is persistence-shaped DB storage only — not a shared history owner
- `MessageRuntime` functions are the shared surface for message/history reads and execution artifact writes

## Mental Model

| Step | Who |
|---|---|
| Identify the project | Project Resolver |
| Prepare the runtime | Project Runtime Binder |
| Hold the bound runtime | Bound Project Runtime |
| Run the workflow | Execution |
| Serve stored state | Persistence |

## Key Clarifications

- Layers are ownership boundaries, not always a single linear chain — different request types may use different subsets
- `BoundProjectRuntime` is not "the workflow" — it is what execution operates on
- Lower layers should shape higher layers, not the reverse — stabilize lower ownership first, then identify stale higher-layer assumptions
- The split between binding and execution matters: binding prepares the runtime, execution uses it
- Layer meaning should be visible in module surface shape — small intentional top-level surface, grouped privileged submodules, internal helpers that do not redefine the public layer contract
