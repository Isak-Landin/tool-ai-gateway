# MCP-Server-Integration

The `ollama/` tool layer is transitioning from hardcoded in-process tool modules to a
dynamic MCP (Model Context Protocol) client-server architecture.

Source of truth: `Gateway-MCP-Server-Data` page in `Docmost-MCP-Service` space.

## Design Principle

All extended tools — those not directly tied to the local system — are owned by external
MCP servers. The gateway acts as the **MCP Host**: it manages one MCP client per
connected server, aggregates tool/resource/prompt data across all servers, and assembles
the complete model input.

**Stays hardcoded (local-system-tied):**

- `return_to_user` — execution lifecycle signal, internal to the gateway
- Git operations (clone, fetch, shell probe) — bound to the local `RepositoryRuntime`

**Moves to MCP servers (extended tools):**

- `web_search` — external data; served by a web-search MCP server
- `list_repository_tree` / `search_repository_text` — candidates for MCP once file
  access is decoupled (or remain bound if local-system access is required)
- `archon_rag_query` / `archon_search` — project knowledge retrieval; served by Archon MCP server
- `switch_repository_branch` — currently orphaned; ownership will be clarified during MCP migration

## MCP Protocol Phases (Gateway Responsibilities)

### Phase 1 — Connection

For each registered MCP server the gateway:

1. Sends `initialize` with `protocolVersion`, `clientInfo`, and supported `capabilities`
2. Receives and stores per-server: confirmed `protocolVersion`, `serverInfo`, declared
   `capabilities` (tools, resources, prompts, logging), and optional `instructions`
3. Sends `initialized` notification to confirm readiness

Nothing beyond initialization is valid until this handshake completes.

### Phase 2 — Discovery

After initialization, for each capability the server declared, the gateway fetches:

| Source | Stored Per Entry |
|---|---|
| `tools/list` | `name`, `title`, `description`, `inputSchema`, `outputSchema`, `annotations` |
| `resources/list` | `uri`, `name`, `title`, `description`, `mimeType`, `annotations` |
| `prompts/list` | `name`, `title`, `description`, `arguments` |

The gateway tracks **which server owns each tool** — `tools/call` must be routed to the
correct server.

Resource and prompt *content* is not fetched at discovery time — only on demand.

### Phase 3 — Assembly (before each model call)

The gateway assembles the full model payload from all connected servers:

| Component | Source |
|---|---|
| System instructions | Merged `instructions` strings from all server initialize responses |
| Tool definitions | Aggregated `tools/list` from all servers (names de-duplicated) |
| Resource content | `resources/read` for selected/relevant resources |
| Prompt messages | `prompts/get` if a prompt template is invoked |
| Conversation history | Gateway-managed prior turns |
| User message | Current input |

Tool name uniqueness across servers is the gateway's responsibility. Where two servers
expose a conflicting name, the gateway must disambiguate (e.g. prefix with server name).

### Phase 4 — Tool Call Routing

When the model returns a tool call:

1. Gateway receives `{ name, arguments }`
2. Gateway looks up owning server from its tool registry
3. Gateway sends `tools/call` to that server
4. Server returns `content` + `isError`
5. Gateway appends result to conversation and re-prompts the model

## Per-Server Persistence (Registration Record)

To support dynamic server addition without hardcoding, the gateway stores per server:

| Field | Description |
|---|---|
| Connection endpoint | URL (Streamable HTTP) or command + args (stdio) |
| Transport type | `http` or `stdio` |
| Auth data | Bearer token, API key, or credential (for HTTP transport) |
| Server name | From `serverInfo.name` post-initialization |
| Protocol version | Confirmed during initialization |
| Declared capabilities | `tools`, `resources`, `prompts`, `logging` flags |
| Server instructions | `instructions` string from initialize response |
| Tool registry | All tool definitions from `tools/list` |
| Resource registry | All resource definitions from `resources/list` |
| Prompt registry | All prompt definitions from `prompts/list` |

Adding a server = store endpoint + auth → run handshake → fetch lists → merge into
aggregate. No hardcoding needed; the protocol provides full discovery.

## Real-Time Updates

Servers that declared `listChanged: true` send notifications when their lists change.
The gateway re-fetches only the affected server's slice:

| Notification | Action |
|---|---|
| `notifications/tools/list_changed` | Re-fetch `tools/list`, update aggregate |
| `notifications/resources/list_changed` | Re-fetch `resources/list` |
| `notifications/prompts/list_changed` | Re-fetch `prompts/list` |
| `notifications/resources/updated` | Re-fetch `resources/read` for changed URI |

## Current State

The current `ollama/tool_registry.py` and `ollama/tool_modules/` are MVP-scope hardcoded
stubs. They are not MCP clients — they are in-process `OllamaToolModule` objects.

The transition to MCP clients is a **post-MVP** architecture target. Until then:

- `return_to_user`, `web_search`, `list_repository_tree`, `search_repository_text` are
  registered and wired in `_get_tool_executors` in `workflow_orchestrator.py`
- `archon_rag_query`, `archon_search`, `switch_repository_branch` exist as orphaned
  modules — registered via `register_tool()` but not imported or wired

## Ownership

- The MCP client layer will live between `Execution` and external tool servers
- `Execution` does not own MCP protocol logic; it consumes aggregated tool definitions
  via the gateway's MCP client manager
- The MCP client manager is a new module, not part of `ollama/` or `tools/`
- `ollama/tool_registry.py` will either be replaced or reused as a thin adapter once
  MCP-provided tool schemas are the primary source
