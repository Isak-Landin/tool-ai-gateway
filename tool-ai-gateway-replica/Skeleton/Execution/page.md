# Execution

The `execution/` package owns all project-scoped workflow orchestration.

Source of truth: `execution/runtime_execution.md`

## Module

`execution/workflow_orchestrator.py` — the single execution entry point for a project-scoped chat run.

## Lifecycle

| Step | Owned By |
|---|---|
| Accept bound runtime + validated input | Execution |
| Validate execution-specific preconditions | Execution |
| Load bounded recent project message history | Execution via `MessageRuntime` |
| Load selected context from `FileRuntime` | Execution |
| Build model-ready envelope | Execution via `ollama/builder` |
| Persist user turn | Execution via `MessageRuntime.store_message_artifact` |
| Execute model call | Execution via `ollama/ollama_client` |
| If tool calls: persist assistant turn, execute tools, persist results, continue | Execution |
| Persist final assistant turn | Execution |
| Return execution result data | Execution → caller |

## What Execution Owns

- workflow ordering
- bounded recent context assembly (limit policy is execution-owned)
- deterministic context selection for the run
- model/tool sequencing
- execution-owned persistence ordering
- the full run cycle until `return_to_user` is called

## What Execution Does Not Own

- project resolution
- runtime binding
- HTTP response shaping
- raw persistence policy
- live file/tree/search outside `FileRuntime`
- message history outside `MessageRuntime` functions

## Dependencies

- `BoundProjectRuntime` — runtime surface for the run
- `MessageRuntime` — bounded history load, sequence load, artifact store
- `FileRuntime.read_file`, `FileRuntime.search_text` — selected context reads
- `ollama/` — envelope building, model call, output parsing
- `tools/` — `execute_return_to_user`, `execute_web_search`, and others (MVP-scope hardcoded)
- MCP client manager (future) — aggregated tool definitions and call routing across MCP servers

See `Skeleton/MCP-Server-Integration` for the intended long-term tool layer.

## MVP Scope

- One model per run
- Bounded recent message window (limit policy in execution)
- Selected context from explicit `selected_files` list via `FileRuntime`
- Run ends when model calls `return_to_user`
- No model-driven history selection
- No full project history by default
- No open-ended execution loops

## Final Intent

Longer-term execution is intended to be retrieval-aware and multi-iteration:

- start with one user goal
- break into runtime-relevant sub-steps
- retrieve additional context when needed
- call tools, retrieval, file access, git, model steps in sequence
- re-evaluate after each important result
- stop when result is sufficient

This is not uncontrolled looping — it is project-scoped, context-aware, multi-iteration runtime that can redirect itself.

## Tool Layer — MVP vs. Final Intent

Current MVP uses a hardcoded `_get_tool_executors` map in `workflow_orchestrator.py`
wired to in-process `OllamaToolModule` callables. This is an interim approach.

Final intent: tool availability is driven by the MCP client manager. Execution receives
aggregated tool schemas and prompt fragments from all connected MCP servers. The call
routing map is built dynamically from the gateway's MCP tool registry, not hardcoded.

Only local-system-tied tools (`return_to_user`, git probes) are candidates for remaining
outside MCP. All extended tools (web search, knowledge retrieval, etc.) should be served
by registered MCP servers.

## Current Issues / Architectural Drift

Documented in `execution/runtime_execution.md` under "Architectural drift to resolve":

- Execution now depends on bound `FileRuntime` surface for selected-context loading; `FilesRepository` and `RepositoryRuntime` are not plausible fallbacks
- `MessagesRepository` is not a plausible fallback for message/history — `MessageRuntime` functions are the correct surface
- Route-facing runtime helpers should expose only `FileRuntime` where needed; message history through `MessageRuntime` functions with explicit repository dependencies
