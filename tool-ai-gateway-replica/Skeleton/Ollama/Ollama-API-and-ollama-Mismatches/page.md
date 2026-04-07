# Ollama API and ollama/ Mismatches

_Active mismatches between the Ollama API behavior and the current `ollama/` implementation._

## Confirmed Mismatches

### 1. Tool call format mismatch

The Ollama API returns tool calls in a nested structure that differs from the flat tool-call shape the current builder and parser expect. Parser may fail to extract tool calls correctly on some model responses.

### 2. System prompt injection point

Current implementation injects the system prompt as a first message in the messages array. Some Ollama model behaviors treat a separate `system` field differently from a system message entry. Behavior may diverge by model.

### 3. Model name normalization

The `config.py` default model name is not validated against the Ollama model registry at startup. A missing or incorrectly named model fails late at call time rather than at boot.

### 4. `parse_model_output` tool-call detection

Current detection relies on presence of specific keys in the assistant response object. Partial or streaming responses may not carry those keys, which would silently skip tool execution.

### 5. Envelope field merging

`merge_chat_envelope_fields(...)` applies field overrides without guarding against overwriting required envelope fields. A caller supplying conflicting override fields can corrupt the envelope before send.

## Status

All five are known but not yet resolved. They are tracked here until addressed or explicitly accepted as current behavior scope.
