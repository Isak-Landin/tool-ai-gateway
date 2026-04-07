# Ollama

The `ollama/` package owns all LLM interaction logic.

## Modules

| File | Purpose |
|---|---|
| `builder.py` | Builds chat envelopes and message structures for model calls |
| `ollama_client.py` | Sends chat envelopes to the Ollama API, parses model output |
| `prompts.py` | Manages system prompt fragments and prompt composition |
| `tool_registry.py` | Builds tool schemas and tool prompt fragments from registered tools |
| `config.py` | Ollama configuration (default model, base URL) |

## Key Functions

- `create_chat_envelope(...)` — creates the base payload for a model call
- `append_*_message(...)` — builder helpers for adding user/assistant/tool/system messages
- `send_chat_envelope(...)` — sends the built envelope to Ollama and returns raw response
- `parse_model_output(...)` — parses assistant message, tool call detection
- `build_tool_schemas(...)` — generates tool schema list from registered tool callables
- `merge_system_prompt_fragments(...)` — composes system prompt from multiple fragments

## Ownership

- Execution is the primary caller
- Execution passes the fully assembled envelope; ollama/ does not own context selection
- Tool schemas are built from `tools/` callables registered at run time
