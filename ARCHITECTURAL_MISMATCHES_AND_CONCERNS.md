# Architectural Mismatches and Concerns

_This document maps MVP blockers, mismatches, and deprecations using the **documented intended solutions** as the source of truth._

_It does not treat current code shape as the authority for what the architecture should be._

## Purpose

This document exists to keep four things explicit:

- active MVP blockers
- newly introduced deprecations caused by intended architecture
- remaining unsolved gaps and inconsistencies
- the documented solution baseline those mappings are derived from

## Source-of-Truth Rule For This Document

For this document:

- the documented intended message/file/tree solutions are the source of truth
- current code is evidence of where deprecations and gaps still exist
- current code is **not** the authority for what the ownership model should be

This matters because the current stage is still mapping-first.

We are documenting:

- what should own responsibility
- what is now deprecated because of that intended ownership
- what still remains unsolved before implementation

## MVP-Critical Active Mismatches and Deprecations

These are the most important current concerns to keep at the top.

### 1. Route-facing file/tree ownership is now partially aligned, but not yet converged across all layers

The intended direction is now:

- one **project-bound, route-serving repository/file surface**

This is now partially implemented through:

- `FileRuntime/FileRuntime.py`
- binding in `ProjectRuntimeBinder`
- holding the bound file surface on `BoundProjectRuntime`

That means the following remain architecturally deprecated as the general owner for route-facing or shared file/tree reads:

- execution-owned repository inspection as the effective general file/tree owner
- case-by-case consumer choice between the bound file surface and execution/tool inspection
- any new route/shared consumer that skips the bound file surface and reads from older seams directly

Current MVP risk:

- execution and any future route/shared consumer can still harden around the wrong owner before the new bound file surface becomes the default seam everywhere

### 2. Message-history ownership is structurally present, but not yet converged onto the intended shape

The intended direction is now:

- `MessagesRepository` refactored into the intentional persistence owner for message reads, writes, and route-usable history shaping
- `ExecutionPersistence` kept focused on execution-owned ordering, bounded recent-history loading, and run artifact persistence
- one bound project-scoped message/history dependency attached during runtime binding

That means the following are now architecturally deprecated:

- letting `ExecutionPersistence` drift into the general route-facing history owner
- duplicating route-facing message/history shaping outside the intended bound message surface
- leaving message ownership split only by caller habit rather than by intended boundary

Current MVP risk:

- message history can still be exposed through the wrong seam even though the lower data support is already strong

### 3. Execution-owned repository tree/search access is now execution-only by intent

The intended direction is now:

- execution-owned repository tree/search usage remains valid for execution/tool behavior
- it should not remain the general owner for route-facing or shared project file/tree reads

That creates explicit new deprecation across existing execution-facing surfaces such as:

- `repository_runtime/inspection/list_tree.py`
- `repository_runtime/inspection/search_text.py`
- `tools/repository/inspection/*`
- execution wiring in `execution/workflow_orchestrator.py`
- tool exposure through `ollama/tool_modules/*`

Current MVP risk:

- these surfaces can still look like the natural lower-layer owner even though the intended architecture now says otherwise

### 4. `BoundProjectRuntime` and `ProjectRuntimeBinder` are now partially aligned, but only on the file side

The intended direction is now:

- one bound file-responsible project surface
- one bound message-responsible project surface
- `BoundProjectRuntime` as holder, not logic owner

The file side of that alignment is now implemented:

- `ProjectRuntimeBinder` binds `FileRuntime`
- `BoundProjectRuntime` holds `file_runtime`

The runtime/binding shape remains incomplete overall because:

This incompleteness is itself a mapped concern because it can hide deprecations in surrounding layers:

- the message side still has no equivalent bound message surface
- execution still uses older direct repository inspection paths instead of the new bound file surface
- routes still do not yet depend on the implemented bound file surface

### 5. Persistence wording and ownership expectations had drifted too broad

The intended direction is now:

- persistence owns persistence-backed artifacts and persistence seams
- persistence does **not** own the general livetime route-serving boundary for project file/tree reads
- `FilesRepository` and `MessagesRepository` should be refactored toward intentional persistence roles

That means the following are now deprecated at the documentation/architecture level:

- broad wording that persistence generically owns live route-facing repository/file access
- treating persistence-shaped objects as the default route-serving lower layer

### 6. Ignore-path and branch-aware semantics are still unattached to the intended file owner

The intended file owner is now known in direction.

But:

- ignore-path behavior is still split between current lower surfaces
- branch-aware route semantics are still not fully attached to one intended route-serving owner

Current MVP risk:

- even with the intended owner mapped, the behavior contract is still incomplete until these semantics are attached to that owner

### 7. MVP usability still depends on converging file and message ownership into one coherent route-facing project flow

The MVP still needs:

- create project
- enter workspace
- load live tree
- load live file content
- load persisted message history
- submit prompt
- persist result
- re-read history and repository state coherently

The current blocker is not missing raw capability.

The blocker is that route work, runtime binding, and shared internal consumers can still drift around the intended message/file ownership model unless the mapped deprecations stay visible.

## Remaining Unsolved Gaps

These remain unsolved even with the intended direction already documented.

### File/tree gaps

- the new file-responsible project-bound surface is not yet documented everywhere else with enough consistency
- other internal consumers that need project tree/file reads do not yet have one obvious intended dependency surface
- ignore-path behavior is still split across current lower surfaces
- branch-aware route semantics are still not fully anchored to the intended file owner
- execution still does not consume the bound file surface
- routes still do not consume the bound file surface

### Message gaps

- the new message-responsible project-bound surface is not yet consistently reflected as the expected route/runtime dependency
- `MessagesRepository` refactor intent still needs to stay explicit so the message side does not fall back to usage-style ownership
- route-facing history shaping still needs to be clearly mapped onto the bound message surface rather than ad hoc querying

### Runtime/binding gaps

- `ProjectRuntimeBinder` is now the binder of the intended project-bound file surface, but not yet the intended message surface
- `BoundProjectRuntime` is now the holder of the intended project-bound file surface, but not yet the intended message surface
- existing layers still visibly reflect the older dependency shape more strongly than the intended one, especially outside binding/runtime

### Cross-layer deprecation gaps

- execution still uses direct `repository_runtime` inspection paths for tool-facing tree/search behavior
- that direct execution-owned access is not wrong for execution/tool behavior, but it is now architecturally deprecated as the general owner for route-facing or shared file/tree reads
- route-level or caller-level duplication is still too easy because the intended bound file/message surfaces are not yet the easiest conceptual seam

## Suggested Solution Mapping

These are the intended solutions that should drive architecture decisions.

They are intentionally placed **below** blockers and deprecations because they are the basis for the mapping, not proof of implementation.

### 1. Introduce one file-responsible project-bound surface

This file-specific object should:

- serve route-facing tree reads
- serve route-facing file-content reads
- serve shared internal project-scoped file/tree consumers
- stay passive
- stay project-scoped
- be bound during project/runtime binding
- be held by `BoundProjectRuntime` or equivalent
- make use of existing runtime repo functions where appropriate
- avoid turning execution/tool wrappers into the ownership boundary

Current implementation note:

- this is now implemented on the file side through `FileRuntime`
- it is bound by `ProjectRuntimeBinder` and held on `BoundProjectRuntime`
- remaining work is adoption across execution/routes and behavior-semantic alignment

### 2. Introduce one message-responsible project-bound surface

This message-specific object should:

- serve ordered route-facing project history reads
- serve shared internal project-scoped message/history reads
- stay passive
- stay project-scoped
- be bound during project/runtime binding
- be held by `BoundProjectRuntime` or equivalent
- reuse persistence-backed message behavior rather than creating route-level duplication

### 3. Refactor `FilesRepository` into an intentional persistence-facing role

`FilesRepository` should no longer define the live route-serving ownership boundary.

Its persistence-facing role should align with persistence concerns rather than live route-serving ownership.

Current implementation note:

- `FilesRepository` has now been narrowed toward DB-shaped file storage/retrieval for MVP
- live repository tree/file serving has moved to the new bound `FileRuntime` surface instead

### 4. Refactor `MessagesRepository` into the intentional persistence owner for message history

`MessagesRepository` should become the persistence owner for:

- message storage
- full ordered history retrieval
- route-usable history shaping

At the same time:

- `ExecutionPersistence` stays execution-owned
- bounded recent-history loading stays execution-owned
- ordered run artifact persistence stays execution-owned

### 5. Keep execution-owned repository access execution-owned

Execution may still use repository runtime behavior for:

- tool calls
- search during execution
- tree inspection during execution
- git/runtime workflow concerns

But that use should stay explicitly execution-scoped.

### 6. Move route expectations onto the intended bound project surfaces

Future route-facing behavior should read from:

- the bound file-responsible project surface
- the bound message-responsible project surface

That keeps routes from:

- duplicating shaping logic
- depending directly on execution internals
- depending directly on persistence internals
- hardening accidental ownership decisions

## Source-of-Truth Context For The Mapping

The following documented solution context is the baseline this file now uses when listing blockers, deprecations, and remaining gaps.

### 1. Message history support

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

- message history is not the main architectural blocker
- a project activity/history route can be supported from existing lower-layer data

Suggested solution:

- refactor `MessagesRepository` into the intentional persistence owner for message reads, writes, and route-usable history shaping
- keep `ExecutionPersistence` focused on execution-owned ordering, bounded recent-history loading, and artifact persistence during runs
- bind a project-scoped message/history dependency during runtime binding
- let `BoundProjectRuntime` hold that bound message surface without becoming the logic owner itself
- let execution orchestrate ordered message use
- let route-facing history reads reuse the bound/history-facing message surface instead of duplicating DB logic

### 2. Live repository file-content behavior now has a bound runtime owner

Current implementation now includes a dedicated runtime file surface.

Evidence:

- `FileRuntime/FileRuntime.py`
- `BoundProjectRuntime.file_runtime`
- `ProjectRuntimeBinder` binding of `FileRuntime`
- `persistence/FilesRepository/FilesRepository.py`

What is now supported:

- project-bound live file reads through `FileRuntime`
- file-content reads delegated through repository-runtime inspection logic
- optional persistence-backed file storage/retrieval through `FilesRepository`
- binding of the file surface during project/runtime binding

Conclusion:

- the behavior exists
- and the intended file-serving owner now exists for the updated binding/runtime layers

Suggested solution:

- keep `FileRuntime` as the live project-bound owner for file-content reads
- keep `FilesRepository` persistence-shaped for DB storage/retrieval rather than live route-serving ownership
- move future route/shared file consumers onto the bound `file_runtime` surface
- avoid turning execution/tool inspection back into the ownership boundary

### 3. Live repository tree behavior now has a bound runtime owner, but execution deprecation remains

Current implementation now includes a dedicated runtime file/tree surface.

Evidence:

- `FileRuntime/FileRuntime.py`
- `BoundProjectRuntime.file_runtime`
- `ProjectRuntimeBinder` binding of `FileRuntime`
- `repository_runtime/inspection/list_tree.py`
- execution/tool wrapper usage from execution

What is already supported there:

- live tree traversal from the current local repository
- repo-relative paths
- ignore-pattern filtering
- project-bound tree access through `FileRuntime`

Conclusion:

- the behavior exists
- and the intended tree/file owner now exists in the updated binding/runtime layers
- but execution still uses direct repository inspection paths for tool behavior and remains the main file/tree deprecation to carry forward

Suggested solution:

- keep tree and file-content ownership together on `FileRuntime`
- let `FileRuntime` keep using existing runtime repo functions without making execution/tool wrappers the ownership boundary
- keep direct execution-owned tree/listing usage scoped to execution/tool behavior rather than treating it as the general file-serving layer
- move future route/shared file-tree consumers onto the bound `file_runtime` surface

Remaining gaps and new deprecations to map:

- execution still uses direct `repository_runtime` inspection paths for tool-facing tree/search behavior
- that direct execution-owned access is not wrong for execution/tool behavior, but it is now architecturally deprecated as the general owner for route-facing or shared file/tree reads
- the new file-responsible project-bound surface is not yet documented everywhere else with enough consistency
- routes and other internal consumers still need to adopt the same bound file surface consistently

## Current MVP Impact

### Project activity/history page

Risk level: **low to medium**

Main remaining concern:

- route-facing history should align to the intended bound message surface rather than fallback seams

### Project workspace tree/file region

Risk level: **medium to high**

Main remaining concerns:

- the intended bound file surface is still missing
- current deprecations are easy to harden if route work starts too early
- ignore and branch semantics still need one intended owner

### Chat history inside workspace presenter

Risk level: **low**

Main remaining concern:

- the route/lower-layer seam must match intended message ownership rather than local duplication

## Bottom Line

The correct reading is:

- lower capability exists
- documented intended ownership is now clear enough to map against
- deprecations must be recorded from that intended ownership, not inferred from current code as if current code were authoritative

The main remaining work in documentation is:

- keep blockers, deprecations, and remaining gaps visible at the top
- keep the message/file/tree solution context preserved lower as the source-of-truth baseline
- keep mapping all new cross-layer deprecations caused by the intended file/message ownership model before implementation starts
