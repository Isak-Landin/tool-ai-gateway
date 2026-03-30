# Architectural Mismatches and Concerns

_This document summarizes currently identified architectural mismatches and concerns around MVP project-page support._

_It is focused on lower-layer support and ownership, not on UI placeholder implementation._

## Purpose

This document exists to capture:

- what is already supported well enough by the current lower layers
- where architectural support exists but ownership is split or unclear
- where future routes can likely be added safely
- where route addition alone would be premature because lower-layer meaning is still ambiguous

## Scope

Focused surfaces:
- project message history
- project execution as persisted history
- live repository tree representation
- live repository file-content representation
- route-facing ownership concerns for those surfaces

Excluded:

- auth and account flows
- UI styling/theming concerns
- MaaS provider design beyond noting model-selection direction

## High-Level Summary

The current lower layers are **closer to ready than broken**.

The main issue is **not** that message history, repo tree, or file content are impossible to support.

The more accurate concern is:

- message history already has a reasonable lower-layer path
- project file/tree route support does **not** yet have the right lower-layer owner
- MVP still requires both of those to work together end-to-end so a user can move from project entry to actual workspace use

This is not best described as two equally valid long-term owners competing.

It is better described as:

- one legacy persistence-shaped file surface that no longer matches intended direction
- one runtime/execution inspection surface that exists for model/tool workflow, not for route-facing project reads
- one missing replacement surface for route-serving, project-bound repository reading

## What Already Appears Strong Enough

## 1. Message history support

Current support is structurally present.

Evidence:

- `db.models.Message`
- `MessagesRepository`
- `ExecutionPersistence`
- execution persistence ordering in `execution/workflow_orchestrator.py`

What is already supported:

- ordered per-project history via `sequence_no`
- persisted user / assistant / tool artifacts
- stored `thinking`
- stored `tool_name` and `tool_calls_json`
- stored `ai_model_name`
- stored timestamps and model-run metadata

Conclusion:

- message history is **not** the main architectural blocker
- a project activity/history route can be supported from existing lower-layer data

Suggested solution:

- refactor `MessagesRepository` into the intentional persistence owner for message reads, writes, and route-usable history shaping
- keep `ExecutionPersistence` focused on execution-owned ordering, bounded recent-history loading, and artifact persistence during runs
- bind a project-scoped message/history dependency during runtime binding
- let `BoundProjectRuntime` hold that bound message surface without becoming the logic owner itself
- let execution orchestrate ordered message use
- let route-facing history reads reuse the bound/history-facing message surface instead of duplicating DB logic

## 2. Live repository file-content behavior exists, but in the wrong shape

Current code does include file-read behavior.

Evidence:

- `persistence/FilesRepository/FilesRepository.py`

What exists there:

- repo-root path scoping
- path escape protection
- single-file reads
- ranged line reads
- total line counts

Conclusion:

- the behavior exists
- but it exists on a persistence-shaped object that no longer fits the intended architecture for route-facing project file access

## 3. Live repository tree behavior exists, but only in an execution/tool-facing path

Current code does include live tree listing behavior.

Evidence:

- `repository_runtime/inspection/list_tree.py`
- tool wrapper usage from execution

What is already supported there:

- live tree traversal from the current local repository
- repo-relative paths
- ignore-pattern filtering

Conclusion:

- the behavior exists
- but it should not be treated as a ready route-facing lower layer because its current purpose is runtime/tool support

## Main Mismatches and Concerns

## 1. The route-serving project repository reader surface is still missing

This is the clearest architectural concern.

There are currently two relevant code paths:

### Legacy persistence/file path

- `FilesRepository`

Current problem:

- it is shaped like a persistence-facing object
- even where it reads live repo state, it still communicates the wrong ownership model for MVP route-serving project reads
- it should not be treated as the livetime server for project tree/file route expectations

### Runtime/execution inspection path

- `repository_runtime/inspection/list_tree.py`
- `repository_runtime/inspection/search_text.py`
- exposed through execution-owned tool behavior

Current problem:

- this path exists to let runtime/tool workflow answer model requests
- it should not automatically become route-facing project read infrastructure

### Concern

The true missing piece is a **project-bound, route-serving repository read surface** for:

- tree listing
- file content reads
- possibly project-scoped repository search later

That surface should be:

- project-scoped
- passive
- bound during runtime binding or equivalent project binding
- not an execution/orchestrator surface
- not a route-shaping surface

Suggested direction:

- treat this as a missing replacement surface, not as a reason to promote either legacy `FilesRepository` or execution/tool inspection into route ownership
- consider attaching that surface onto `BoundProjectRuntime` or an equivalent bound project dependency holder so route-serving project reads stay project-scoped without turning runtime itself into an orchestrator

## 2. Ignore-path handling is still a real concern

This is a concrete mismatch, not only a theoretical one.

### Runtime inspection surface

- respects configured ignore patterns from `repository_tools/ignored_paths.json`

### FilesRepository surface

- does **not** apply the same ignore-path filtering for `list_tree(...)` or `read_file(...)`

### Why this matters

If future project routes are built on top of `FilesRepository` behavior before the replacement surface exists, the UI may get:

- different visibility rules than execution/tool behavior
- different file availability rules
- weaker safety guarantees than intended route-serving project reads should have

Conclusion:

- current lower-layer behavior is **not yet unified**
- any future replacement project-bound repository reader should adopt one intentional ignore-path policy

## 3. Route-facing live repo reads do not yet have the right ownership model

There is still a missing ownership boundary for route-serving project file/tree access.

### Why this matters

For MVP project workspace routes, the UI wants:

- live repo tree
- live file content
- consistent behavior relative to the active project runtime

But right now the available code paths are both wrong for route ownership:

- `FilesRepository` is the wrong shape
- runtime inspection is the wrong purpose

Conclusion:

- support behavior exists
- the intended route-serving owner is still missing

## 4. Branch-aware repo representation is not yet fully guaranteed for future standalone routes

The system currently supports:

- stored project default branch
- runtime branch override
- bound runtime construction with an effective branch value

But that does **not** automatically mean all future route-facing repo reads are truly branch-aware.

### Why

The current legacy file path reads directly from `repo_path` on disk.

That means:

- it reads whatever the working tree currently is
- it does not itself bind through runtime
- it does not itself enforce branch override semantics

Meanwhile:

- runtime-bound repo behavior exists separately for execution/tool work

Conclusion:

- branch-aware route expectations are **not fully architecturally guaranteed** yet for standalone repo routes
- this is especially relevant if future UI routes expect branch dropdown changes to affect repo tree/file responses immediately

## 5. Message-history ownership is available, but split by usage style

There are currently two meaningful message surfaces:

### `MessagesRepository`

Strength:

- good fit for full ordered project history

### `ExecutionPersistence`

Strength:

- good fit for execution-owned bounded recent history and ordered artifact persistence

### Concern

These are compatible, but they represent slightly different use cases:

- full project history for activity/history page
- bounded recent context for execution

Conclusion:

- history support exists
- route-facing ownership still needs one clear decision:
  - full-history route should likely align to a dedicated history-facing persistence seam
  - execution should keep owning bounded recent-history loading for runtime behavior

Suggested solution:

- use a refactored `MessagesRepository` as the persistence owner for message storage/retrieval and route-usable history structuring
- keep execution-oriented message behavior in `ExecutionPersistence` where ordered run persistence and bounded context still belong
- have runtime binding attach the project-scoped message/history component onto the bound project runtime as a dependency
- let routes consume that bound/history-facing surface rather than building separate message queries or shaping logic ad hoc

## 6. MVP end-to-end usability still depends on joining these concerns correctly

Even with the ownership correction above, the MVP still needs a coherent start-to-end project flow:

- create project
- enter project workspace
- load live tree
- load live file content
- load persisted message history
- submit a prompt
- persist and later re-read resulting history

That means the documentation should keep both truths visible:

- message/history support is already relatively strong
- route-serving project repository reads still need the correct lower-layer owner

The concern is not only architectural neatness.

It is also whether MVP can support a coherent usable workspace without later route rewrites.

## 7. Route absence is not the same as lower-layer absence

This is important enough to state explicitly.

Missing routes do **not** mean missing core behavior for:

- project message history
- live repo tree
- live file-content reading

The more accurate reading is:

- message-history lower support mostly exists
- file/tree behavior exists in partial or wrong-shaped places
- route-serving ownership decisions are the missing pieces

## Current Impact on MVP UI/API Integration

## Project activity/history page

Risk level: **low to medium**

Why:

- data exists
- message persistence exists
- sequence ordering exists

Main remaining concern:

- choosing the intended lower-layer history surface for route exposure

## Project workspace tree/file region

Risk level: **medium**

Why:

- data exists
- live reads exist

Main remaining concerns:

- the proper route-serving project-bound repository read surface does not yet exist
- `FilesRepository` should not silently become that livetime route-serving surface by accident
- runtime inspection should not silently become that livetime route-serving surface by accident
- ignore handling and branch semantics still need to be designed onto the replacement surface
- the eventual replacement surface must still return the exact kinds of tree/file data the workspace needs, not only satisfy ownership purity

## Chat history inside workspace presenter

Risk level: **low**

Why:

- message data is structurally strong
- execution already persists the needed artifacts

Main remaining concern:

- exposing the right route shape rather than inventing data locally in UI

## Recommended Reading of the Situation

The correct interpretation is:

- **message history:** architecturally supported
- **live file/tree behavior:** present, but not yet housed in the right route-serving lower-layer owner
- **route-layer support:** incomplete
- **replacement project-bound repository read surface:** still missing
- **MVP concern:** both history support and repository-read support must converge into one coherent route-facing project experience

So the next architectural risk is not “we lack the data.”

It is:

- “we may expose routes on top of legacy or wrong-purpose lower-layer behavior unless we define the correct project-bound reader surface first”

## Concrete Concerns to Carry Forward

1. Define a dedicated project-bound repository read surface for route-serving tree/file access.

2. Keep that surface passive:

- no route shaping
- no orchestration
- no model/tool workflow ownership

3. Unify ignore-path behavior on that replacement surface.

4. Clarify whether standalone repo tree/file routes must honor runtime branch override semantics.

5. Keep full project history and bounded execution history conceptually separate, even if they share the same underlying `messages` table.

6. Make sure the eventual replacement surface returns the real workspace-needed data shape:

- tree entries
- file content
- line ranges / counts where needed
- repo-relative identities

7. Avoid treating current UI placeholders or current execution/tool helpers as proof that route ownership is already solved.

## Bottom Line

The system is **not missing fundamental architectural support** for MVP project-page needs.

The real issues are:

- the intended route-serving project-bound repository reader surface does not exist yet
- `FilesRepository` is the wrong shape for that **livetime route-serving** responsibility
- runtime inspection is the wrong purpose for that responsibility
- ignore behavior and branch-aware semantics still need to be designed onto the replacement surface
- MVP still requires those concerns to be solved in a way that supports real workspace loading, history re-reading, and prompt continuation
- explicit route exposure should happen only after that ownership is made clear

That is a better problem than missing core capability, but it still needs to be recorded clearly so future route work does not harden the wrong ownership boundary.
