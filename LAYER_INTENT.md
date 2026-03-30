# Layer Intent

_This document explains the five internal layers as concepts, not as code._

_The goal is to describe what each layer means, what it owns, and how the full runtime process can move through them without treating the architecture as one rigid, always-linear chain._

## Layer 1: Project Resolver

### What it is

Project Resolver is the layer that answers one narrow question:

**"Which project is this request talking about?"**

It exists to identify and confirm the project that later runtime work may depend on.

### What it owns

- deciding whether a project exists
- identifying the correct stored project record
- handing that project identity upward in a usable form

### What it does not own

- building runtime dependencies
- deciding how the project should be used during a run
- executing workflow
- shaping a response to the user

### Why it exists as its own layer

The system should not mix "finding the project" with "doing work on the project."

Those are different responsibilities.  
If they are mixed together, the system becomes harder to reason about and easier to break when runtime behavior evolves.

## Layer 2: Project Runtime Binder

### What it is

Project Runtime Binder turns a resolved project into a usable runtime surface.

It answers the question:

**"Given this project, what dependencies should be attached so runtime work can happen?"**

### What it owns

- creating a project-scoped runtime representation
- attaching the dependencies needed for runtime work
- returning one bound runtime surface that later layers can use

### What it does not own

- deciding what the workflow should do
- resolving the project in the first place
- storing business logic about the run itself
- shaping user-facing responses
- acting as the live lower-layer owner for project file/tree/search reads outside intentional bound objects such as `FileRuntime`

### Why it exists as its own layer

A resolved project is not yet a usable runtime.

A project may need attached dependencies such as:

- project-scoped persistence surfaces
- project-scoped repository execution surfaces
- other runtime-only dependencies

Binding is the act of preparing that runtime shape without yet performing the work itself.

## Layer 3: Bound Project Runtime

### What it is

Bound Project Runtime is a project-scoped runtime container.

It is not a workflow.  
It is not a decision-maker.  
It is not a resolver.

It is simply the runtime representation of one project plus its already bound dependencies.

### What it owns

- holding project-scoped runtime state
- exposing already bound dependencies
- providing one stable runtime object during a run
- allowing cleanup of bound resources when needed

### What it does not own

- deciding what to do next
- loading persistence by itself
- constructing dependencies by itself
- interpreting user requests

### Why it exists as its own layer

The runtime needs one stable object that represents:

- which project is active
- which branch or repository root is active
- which project-scoped dependencies are already attached

That object should be passive.

Its job is to hold the runtime shape, not to act as a hidden orchestrator.

## Layer 4: Execution

### What it is

Execution is the first layer that actually runs project-scoped workflow.

It answers the question:

**"Now that we have a usable project runtime, what should happen in what order?"**

### What it owns

- runtime ordering
- context assembly
- message processing during the run
- selected context loading for the run
- deciding which tools belong in the run
- model and tool sequencing
- execution-owned persistence ordering
- deciding when the run is finished

### What it does not own

- identifying the project
- binding the project runtime
- shaping transport responses
- pretending to be raw storage

### Why it exists as its own layer

This layer is where decisions about the run belong.

For example:

- what context should be included
- what tools should be available
- whether a tool should be called
- what gets persisted and in what order
- when the system should stop and return a result

This is orchestration.

That responsibility should not leak upward into request handling or downward into persistence.

## Layer 5: Persistence

### What it is

Persistence is the serving layer for stored state and persistence-backed project artifacts.

It answers the question:

**"How do we read or write the state that higher layers need?"**

### What it owns

- reading stored entities
- writing stored entities
- storing and serving project message/history artifacts needed by MVP execution
- storing persistence-backed file/archive artifacts where needed
- serving execution-facing storage needs
- serving runtime-binding-facing storage needs
- providing persistence seams reused by bound project message/file surfaces

### What it does not own

- deciding what the workflow should do
- deciding what context should be chosen
- binding runtime behavior
- interpreting the user's goal
- acting as the intended livetime route-serving owner for project tree/file reads
- acting as the intended livetime route-serving owner for project message/history reads

### Why it exists as its own layer

Storage and workflow are different concerns.

Persistence should serve state.  
Execution should decide how to use state.

If persistence starts deciding runtime behavior, the architecture becomes blurred and debugging becomes much harder.

Current file-side clarification:

- `FilesRepository` is persistence-shaped DB storage/retrieval only
- `FileRuntime` is the lower live owner for project-scoped file reads, tree reads, ignore-path enforcement, and branch-aware repository access
- `RepositoryRuntime` remains shell/git transport only and is not a live file/tree owner
- callers should not unwrap `FileRuntime` back into `RepositoryRuntime`; direct `FileRuntime.repository_runtime` access is deprecated
- older direct inspection or self-managed file-loading seams have been removed from the live dependency path and should not be reintroduced as alternative lower owners
- `FilesRepository` and `RepositoryRuntime` now fail explicitly if called like live file/tree owners instead of persistence/transport surfaces
- explicit storage-shaped names such as file-row access and persistence-repository builders should be preferred over generic names that blur live-serving ownership

Current message-side clarification:

- `MessagesRepository` is persistence-shaped DB storage/retrieval only
- `MessageRuntime` is the lower live owner for project-scoped history reads and execution-reused ordered message access
- callers should keep message/history reads on `MessageRuntime` instead of reaching sideways for lower persistence or other runtime dependencies
- older caller-shaped history seams have been removed from the live dependency path and should not be reintroduced as alternative lower owners
- `MessagesRepository` now fails explicitly if called like a shared message/history owner instead of a persistence surface
- explicit storage-shaped names should be preferred over generic names that blur live-serving ownership

Current bound-runtime clarification:

- `BoundProjectRuntime` is a holder, not a broad dependency bag for ad hoc caller behavior
- direct `BoundProjectRuntime.repository_runtime`, `BoundProjectRuntime.file_runtime`, and `BoundProjectRuntime.message_runtime` access is deprecated
- callers should use the explicit `require_*_runtime()` accessors so code states which lower surface it actually intends to consume
- route-facing helpers should prefer a narrowed route runtime that exposes only the bound `FileRuntime` and `MessageRuntime` surfaces needed for live reads

## Clarification 1: Layers are ownership boundaries, not always a single chain

It is easy to imagine layers as if every request must always pass through all five in a perfectly straight line.

That is not the real idea.

The better mental model is:

- each layer owns a different kind of responsibility
- some runtime branches may involve several layers
- some branches may involve only a subset of them
- a layer may exist in the architecture even when a specific request does not need it

So the architecture is not "one fixed pipeline."

It is a set of responsibility boundaries that can be combined differently depending on the kind of request.

## Clarification 2: Different branches of runtime may not touch the same layers

Some runtime paths may need:

- project identification
- runtime binding
- execution
- persistence

Other paths may need only:

- request handling
- persistence

And some future paths may use one execution branch that never touches another branch's dependencies at all.

This is normal.

The point of the layer split is not to force sameness.  
The point is to keep responsibility clear wherever the path goes.

## Clarification 3: Project Handle is not "the workflow"

Bound Project Runtime can be especially confusing if your mind expects a linear workflow object.

It helps to think of it this way:

- Project Resolver says **which project**
- Project Runtime Binder says **what runtime dependencies are attached**
- Bound Project Runtime holds the result of that preparation
- Execution decides **what to do with it**

So Bound Project Runtime is not another stage of decision-making.  
It is the runtime object that later decisions operate on.

## Clarification 4: Lower layers should shape higher layers, not the reverse

When lower layers are being stabilized, they should not be bent to match outdated higher-layer assumptions.

The better rule is:

- stabilize the lower ownership boundary
- expose what that layer should really mean
- identify which higher-layer expectations are now stale
- decide later whether those higher layers should be updated, tracked, or removed

This avoids building technical debt around deprecated assumptions.

## Clarification 5: The split between Runtime Binding and Execution matters

One of the easiest mistakes is to let Project Runtime Binder start behaving like Execution.

The difference is:

- Project Runtime Binder prepares the runtime
- Execution uses the runtime

## Clarification 6: Layer meaning should be visible in the module surface

As the codebase grows, it becomes harder to protect layer intent if an entire layer is represented by one growing file or one flat object with many mixed responsibilities.

The better long-term shape is:

- a small intentional top-level surface for the layer
- clearly grouped privileged or ownership-specific submodules
- internal helpers that do not redefine the public meaning of the layer

This matters because the top-level module surface becomes the architectural equivalent of a reachable endpoint.

It should communicate:

- what this layer is for
- what kinds of entrypoints are intentionally reachable
- which lower-level details are only internal support

For example, a layer may later benefit from separating:

- normal top-level layer entrypoints
- use-specific surfaces intended for one owning higher layer
- internal utility submodules that should not be treated as part of the layer contract

The goal is not to build rigid caller policing everywhere.

The goal is to make layer ownership visible in structure so that:

- intentionally reachable entrypoints stay import-safe and structurally stable
- bootstrap/config validation does not get confused with normal application entrypoint behavior

- the intended usage is intuitive
- growth does not collapse back into one oversized object
- privileged behavior can be grouped intentionally instead of leaking across the full layer
- tests and review can enforce the smaller public surface more easily

Binding should answer:

**"What should be attached?"**

Execution should answer:

**"What should happen now?"**

Those are not the same kind of responsibility.

## Runtime Walkthrough: From user request to response

This section describes the process conceptually, without tying it to any specific implementation.

### Step 1: A user makes a request

A user asks the system to do something.

That request might be:

- project-scoped
- non-project-scoped
- simple
- workflow-heavy

Not every request needs the same branch of the architecture.

### Step 2: The system decides whether a project is involved

If the request is not about a specific project, the project-scoped layers may not be needed at all.

If the request is project-scoped, the system first needs to know which project is being targeted.

That is where Project Resolver becomes relevant.

### Step 3: The project is resolved

The system identifies the project and confirms that it exists.

At this point, the system knows **which project** it is dealing with, but it still does not yet have a usable runtime.

### Step 4: A runtime is bound for that project

Now the system prepares a project-scoped runtime.

This means attaching the dependencies needed for later work, such as:

- project-scoped persistence surfaces
- project-scoped repository behavior
- other runtime-needed dependencies

The result is one bound project runtime.

### Step 5: The bound runtime is held in one stable project representation

Instead of passing loose values everywhere, the system keeps one runtime representation for the active project.

That representation is the Bound Project Runtime.

It exists so that later workflow can operate against one stable project-scoped runtime surface.

### Step 6: Execution decides what the run should do

Once the bound runtime exists, Execution can begin.

Execution decides things like:

- what context should be loaded
- what selected files or repository state matter
- what tools should be available
- whether the model should answer directly or use tools first
- what should be persisted and when

This is where the runtime becomes an actual workflow.

### Step 7: Persistence serves the state needed during the run

As Execution runs, it asks Persistence for the state it needs.

That may include:

- recent message history
- execution-owned stored artifacts
- scoped repository/file state

In the intended split:

- execution now performs bounded recent-history loading and ordered artifact persistence through `MessageRuntime`
- `MessageRuntime` is the bound project-scoped message surface for route/shared reads and execution-owned ordered message work
- route-style history access belongs on the bound `MessageRuntime`

Persistence does not decide the workflow.  
It serves the workflow.

### Step 8: Execution keeps ordering the run until a result exists

Execution may:

- prepare the model input
- call the model
- receive tool requests
- execute tools
- persist tool results
- continue the run

It keeps doing the work in controlled order until there is either:

- a sufficient result
- or a clear execution-layer error

### Step 9: A result is returned upward

Once Execution finishes, the result travels back upward.

The runtime-specific work is now complete.

Higher layers may then turn that result into whatever final response shape the user receives.

### Final mental model

The full process is best understood like this:

- Project Resolver identifies the project
- Project Runtime Binder prepares the runtime
- Bound Project Runtime holds the bound runtime
- Execution runs the project-scoped workflow
- Persistence serves the state needed by that workflow

This is not just a sequence of files.

It is a split of meaning:

- **identify**
- **prepare**
- **hold**
- **run**
- **serve state**
