# Ollama — MVP and Final Intent

## Current MVP

The Ollama package is functional for MVP scope:

- builds chat envelopes with system prompt, user/assistant history, and selected context
- sends to local Ollama instance
- receives and parses model output including tool call detection
- tool schemas are dynamically generated from registered tool callables
- system prompt is assembled from fragments (base + tool guidance)

MVP uses one model per run. The model name is determined by config default or per-run override.

## Final Intent

### Multi-model routing

Long-term intent is to support routing across multiple LLM backends beyond Ollama (e.g. cloud models, other local runtimes). Envelope building should remain backend-agnostic; only the send step changes.

### Streaming

Current MVP uses non-streaming responses. Future intent includes streaming output delivery to the UI for progressive display.

### Context-aware model selection

The final runtime may allow model selection driven by execution context — e.g. tool-heavy runs choosing a stronger model automatically. That decision lives in Execution, not in ollama/.

### Tool Registry evolution

Current tool registry builds schemas from callables registered at call time. Long-term the registry should support dynamic tool discovery scoped to the project runtime.
