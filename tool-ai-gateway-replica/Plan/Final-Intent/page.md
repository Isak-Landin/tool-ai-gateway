# Plan — Final Intent

_Long-term product and architecture intent for tool-ai-gateway._

## Product Vision

A project-scoped AI development assistant that:

- connects to a real Git repository (local clone, SSH access)
- understands the repository through live file reads, tree navigation, and text search
- runs multi-step, context-aware, tool-using AI sessions scoped to one project
- persists the full ordered session history per project
- allows users to manage projects, switch branches, and control the AI runtime

## Architecture Final Intent

### Execution

Execution evolves from a single ordered chat run to a retrieval-aware, multi-iteration runtime:

- start with one user-facing goal
- break into runtime-relevant sub-steps
- retrieve additional context when current path is insufficient
- call tools, retrieval, file access, git, model steps in sequence
- re-evaluate after each important result
- stop when sufficient result or clear execution error

Not uncontrolled looping — bounded, project-scoped, context-seeking execution.

### Layer Shape

Each layer should converge toward a small intentional top-level surface:

- clearly grouped privileged submodules for use-specific behavior
- internal helpers that do not redefine the public layer contract
- naming that reflects ownership so drift feels wrong before tests catch it

### Persistence

Full project execution history (messages, tool calls, file snapshots, activity events) stored durably. Separated by type and owner (messages to `MessagesRepository`, files to `FilesRepository`, activity to a future dedicated surface).

### File and Repository

- `FileRuntime` as the stable live file/tree/search owner for all project-scoped reads
- `RepositoryRuntime` as transport only
- Future: `list_tree` and `load_selected_context` reintroduced once lower ownership split is clarified

### User Accounts

User accounts are expected in final intent:

- login / register / session management
- per-user project access and ownership
- invitation and access control
- user preferences

### MCP Tool Integration

All extended tools — those not directly tied to the local system — are served by
registered MCP (Model Context Protocol) servers. The gateway acts as the **MCP Host**:

- manages one MCP client per connected server
- discovers tools, resources, and prompt templates dynamically via the MCP protocol
- aggregates tool schemas from all servers into a single flat list for the model
- routes tool calls to the owning server at execution time
- supports dynamic server addition without code changes (registration record in DB)

**Local-system-tied tools** (`return_to_user`, git probes) may remain in-process.
**Extended tools** (web search, knowledge retrieval, branch management, etc.) are MCP
server responsibilities.

This replaces the current hardcoded `OllamaToolModule` / `_get_tool_executors` pattern.
The MCP client manager is a new module layer between `Execution` and external tool servers.

See `Skeleton/MCP-Server-Integration` for the full protocol phase breakdown and
per-server persistence requirements.

### Multi-model Routing

Long-term support for routing across multiple LLM backends (local Ollama, cloud models). Envelope building stays backend-agnostic; only the send step changes by model type.

## Current Distance from Final Intent

| Area | Current State | Final Intent |
|---|---|---|
| Execution | Single ordered run, MVP scope | Multi-step retrieval-aware runtime |
| Persistence | Message and file rows | Full activity event feed + richer history |
| UI | Project workspace + shell auth pages | Full auth, accounts, sync controls, activity timeline |
| Branches | Freeform input, no enumeration | Authoritative branch list from backend |
| Models | Single configured Ollama model | Multi-model routing with per-run selection |
| Tools | Hardcoded in-process modules (MVP) | Dynamic MCP server discovery |
| Auth | None | Full user account system |
