# Runtime Execution

_Quick overview of how project-scoped execution is intended to run._

## Lifecycle

The execution lifecycle starts when a caller above the execution layer provides:

- a bound project runtime
- validated execution input

The execution lifecycle ends when execution returns:

- final execution result data
- or an execution-layer error

Between those points, execution owns the runtime workflow.

## Runtime Process

| Step | Purpose |
| --- | --- |
| **1. Accept run** | Receive a bound runtime and execution input |
| **2. Validate run** | Check execution-specific requirements |
| **3. Load state** | Load prior messages, selected context, and other project-scoped state |
| **4. Prepare run** | Decide available tools, build model-ready input, determine next action |
| **5. Execute cycle** | Run model, tool, retrieval, or runtime sub-processes as needed |
| **6. Persist artifacts** | Persist user, assistant, tool, and other execution-owned artifacts in order |
| **7. Return result** | Return final execution result data upward |

## MVP

The first version should stay narrow.

### Scope

- accept a bound runtime and validated chat input
- accept an optional execution-time `ai_model_name` override for the run
- load a bounded recent project message window
- load selected project context from the current local repository state
- choose context deterministically inside execution
- prepare one model-ready run
- persist the user turn
- execute the model call
- if tool work is used, execute it in controlled order
- persist resulting assistant and tool artifacts
- return a final execution result

### MVP Boundaries

- one execution model for the run
- no model-driven history selection
- no full project-history payload by default
- no broad autonomous runtime planning
- no open-ended execution loops
- no deep self-redirection into many sub-processes
- no large execution graph

The MVP goal is a reliable, ordered project-scoped run with bounded context.

### MVP Message Processing Requirement

- message processing is required MVP behavior, not optional future polish
- execution must load recent project messages as bounded run context
- execution must persist user, assistant, and tool artifacts in ordered sequence
- persisted message artifacts must retain the actual `ai_model_name` used for the run so model choice remains historically visible even if later runs use a different model

### Current MVP Selected Context Rule

- `selected_files` is treated as a list of repo-relative paths
- execution loads selected context from the current local repository state
- execution does not rely on persisted file snapshot rows for selected context
- selected context should remain project-scoped and branch-aware because it comes from the bound local repo
- shell-backed tools should run from one bound repo-root shell with repo-relative paths
- branch switching is not part of the current MVP execution tool set
- execution returns control to the user only when the model calls `return_to_user`

### Architectural drift to resolve before broader file-route work

- execution currently reaches repository tree/search behavior through execution-owned runtime helpers
- that remains valid for execution/tool behavior
- but it should now be treated as architecturally deprecated for general file/tree serving once the dedicated bound file surface exists
- route-facing or shared project file/tree reads should move toward the bound file-responsible surface instead of expanding direct execution ownership

## Intention

The longer-term intention is broader than a single linear chat run.

### Intended Runtime Behavior

- retrieval-aware execution
- multi-step project-scoped reasoning
- iterative tool usage
- cross-reference gathering during a run
- interruption of a current sub-process when missing context is discovered
- return to the interrupted task after enough context has been gathered

### Intended Execution Style

Execution should be able to:

- start with one user-facing goal
- break that goal into runtime-relevant sub-steps
- retrieve additional context when the current path is insufficient
- call tools, retrieval, file access, git, or model steps in sequence
- re-evaluate the next best step after each important result
- stop only when the run has produced a sufficient result or a clear execution error

This is not meant to be uncontrolled looping. The intention is a project-scoped, context-aware, multi-iteration runtime that can redirect itself when needed.

## Ownership

Execution owns:

- runtime ordering
- context assembly
- retrieval and tool sequencing
- execution-owned persistence ordering
- deciding when more context is needed during a run

Execution does not own:

- project resolution
- runtime binding
- raw persistence policy
- HTTP response shaping
- the general lower-layer ownership boundary for route-facing project file/tree reads

## Practical Reading

If the question is:

| Question | Answer |
| --- | --- |
| **Who starts execution?** | A caller above the execution layer |
| **What does execution receive?** | A bound runtime and validated execution input |
| **What does execution control?** | The runtime workflow until completion |
| **What does execution return?** | Final result data or an execution-layer error |
| **What is MVP?** | One reliable ordered run with bounded recent project context |
| **What is the real intention?** | Retrieval-aware, multi-iteration, context-seeking execution |
