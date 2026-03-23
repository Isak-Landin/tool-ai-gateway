# Ollama Architecture Intent

## MVP

### Goal

Provide one reliable Ollama chat surface that matches the real `/api/chat` structure closely enough for MVP execution work.

### MVP Runtime Behavior

- accept a model-ready chat envelope
- support bounded recent project history
- support explicit tool inclusion decided by execution
- support one execution model per run
- support non-streaming final-body handling
- support tool-call detection from Ollama responses
- support appending tool results back into the next chat envelope

### MVP Architecture Shape

- envelope-first chat building
- explicit tool registration
- explicit schema building
- explicit prompt-fragment merging
- clear separation between:
  - payload building
  - Ollama transport
  - tool/spec registration

### MVP Boundaries

- no fully autonomous runtime planner inside `ollama/`
- no hidden context policy inside `ollama/`
- no project-specific execution logic inside `ollama/`
- no second model for context selection

Execution decides runtime policy.  
`ollama/` builds and sends correct chat envelopes.

## Final Intent

### Goal

Make `ollama/` easy to extend for richer runtime behavior without rewriting its base surfaces.

### Final Runtime Behavior

- build chat envelopes dynamically as runtime state changes
- append messages, tool calls, tool results, and future fields cleanly
- allow richer runtime spec assembly during execution
- support iterative multi-step runs without inventing a parallel chat interface

### Final Architecture Shape

The intended architecture should feel closer to a registry/composition system:

- register tools
- register specs
- allow partial spec composition
- merge prompt/spec fragments at runtime
- append envelope fields without reshaping the whole request model each time

### Final Intent Rules

- remain coherent with Ollama `/api/chat`
- do not replace Ollama's native chat structure with a project-only interface
- make new fields appendable instead of hardcoded into one narrow path
- keep project runtime policy in execution, not in `ollama/`

### Future-Friendly Fields

Even if not used immediately, the structure should remain easy to expand for:

- `messages`
- `messages.tool_calls`
- `messages.tool_name`
- `images`
- `thinking`
- future prompt/spec fragments

